from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import ClassVar

from pxbuild.models.input.pydantic_pxbuildconfig import PxbuildConfig
from pxbuild.models.input.pydantic_pxmetadata import AttachmentItem, PxMetadata
from pxbuild.models.input.pydantic_pxstatistics import PxStatistics
from pxbuild.models.middle.dims import Dims
from pxbuild.models.output.pxfile.px_file_model import PXFileModel
from pxbuild.operations_on_model.output.validator.validate_px import Validate

from .helpers.datadata_helpers.datadatasource import Datadatasource
from .helpers.datadata_helpers.main_data import MapData
from .helpers.datadata_helpers.pandas_spark_backend._backend_methods import (
    IBackendMethods,
)
from .helpers.datadata_helpers.pandas_spark_backend.pandas_spark_backend import (
    create_backend,
)
from .helpers.loaded_jsons import LoadedJsons
from .helpers.logger_config import configure_logger, logger
from .helpers.support_files import SupportFiles


@dataclass
class ValidationSummary:
    """Lightweight, serializable summary of a Validate() run for one built PXFileModel."""

    is_valid: bool
    passed_count: int
    failed_count: int
    errors: list[str] = field(default_factory=list)

    @classmethod
    def from_validate(cls, validation: Validate) -> "ValidationSummary":
        return cls(
            is_valid=validation.is_valid(),
            passed_count=len(validation.passed),
            failed_count=len(validation.failed),
            errors=[str(rep) for rep in validation.failed],
        )


class PxBuildValidationError(ValueError):
    """Raised when an invalid PX model is about to be written."""

    def __init__(self, validation_by_language: dict[str, ValidationSummary]) -> None:
        self.validation_by_language = validation_by_language
        details = []
        for language, summary in validation_by_language.items():
            if not summary.is_valid:
                details.append(f"Language {language}:\n" + "\n".join(summary.errors))
        message = "PX model validation failed; no files were written."
        if details:
            message += "\n" + "\n".join(details)
        super().__init__(message)


@dataclass
class PxBuildStatistics:
    """Statistics about a build, deliberately excluding the (potentially huge) DATA values.

    row_count/cell_count both describe the number of data cells actually written
    (they are the same number for this file format: one row == one cell). matrix_size
    is the theoretical size implied by the dimensions/codelists and should equal
    row_count/cell_count for a well-formed build.
    """

    languages: list[str]
    decimals: int | None = None
    matrix_size: int | None = None
    row_count: int | None = None
    cell_count: int | None = None
    build_seconds: float | None = None
    write_seconds: float | None = None
    output_files: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        return (
            f"Languages: {self.languages}\n"
            f"Decimals: {self.decimals}\n"
            f"Matrix size: {self.matrix_size}\n"
            f"Row count: {self.row_count}\n"
            f"Cell count: {self.cell_count}\n"
            f"Build seconds: {self.build_seconds}\n"
            f"Write seconds: {self.write_seconds}\n"
            f"Output files: {', '.join(self.output_files)}"
        )


@dataclass
class PxBuildModel:
    """Result of building a PX file: the in-memory model plus statistics/validation.

    ``models_by_language`` maps each built language code to its
    :class:`PXFileModel`, or contains a single ``"multi"`` entry when the
    config asked for one multilingual file. Typed keyword access is available
    on the built PXFileModel(s) directly (e.g. ``model.get_model().title.get_value()``),
    or via the convenience properties below (``.title``, ``.contents``, ...),
    which read from the model's main language. DATA is never eagerly copied
    here: only aggregate counts are captured in ``statistics``.

    Pass this to :func:`write_px_file` to write it to disk (or use
    :func:`build_px_file` to do both steps in one call).
    """

    pxmetadata_id: str
    models_by_language: dict[str, PXFileModel]
    config: PxbuildConfig
    dims: Dims
    pxmetadata: PxMetadata
    output_filename: str
    backend: "IBackendMethods"
    main_language: str
    statistics: PxBuildStatistics
    validation_by_language: dict[str, ValidationSummary]

    def get_model(self, language: str | None = None) -> PXFileModel:
        """Return the built PXFileModel for a language, or the main/only one built."""
        key = language or ("multi" if "multi" in self.models_by_language else self.main_language)
        return self.models_by_language[key]

    @property
    def is_valid(self) -> bool:
        return all(summary.is_valid for summary in self.validation_by_language.values())

    @property
    def table_id(self) -> str:
        return self.get_model().tableid.get_value()


class _PxModelBuilder:
    """Builds the in-memory PXFileModel(s) for a pxmetadata id.

    This class only reads input JSONs/data and populates PXFileModel
    instances; it never writes to disk. Use build_px_model()/build_px_file()
    (module-level functions below) instead of instantiating this directly.
    """

    LabelConstructionOptionDict: ClassVar[dict[str, int]] = {
        "LabelConstructionOption.code": 0,
        "LabelConstructionOption.text": 1,
        "LabelConstructionOption.code_text": 2,
        "LabelConstructionOption.text_code": 3,
    }

    PriceTypeDict: ClassVar[dict[str, str]] = {"PriceType.current": "C", "PriceType.fixed": "F"}

    def __init__(
        self, pxmetadata_id: str, config_file: str | dict, backend: str = "pandas", debug: bool = False
    ) -> None:
        configure_logger(debug)
        self._backend: IBackendMethods = create_backend(backend)

        self._pxmetadata_id = pxmetadata_id

        self._loaded_jsons: LoadedJsons = LoadedJsons(pxmetadata_id, config_file)

        self._config = self._loaded_jsons.get_config()
        self._pxmetadata_model = self._loaded_jsons.get_pxmetadata()
        self._pxstatistics = self._loaded_jsons.get_pxstatistics()

        if isinstance(self._pxmetadata_model.dataset.data_file, str):
            file_id = self._pxmetadata_model.dataset.data_file
        elif isinstance(self._pxmetadata_model.dataset.data_file, dict):
            file_id = next(iter(self._pxmetadata_model.dataset.data_file))
        self._datadata = Datadatasource(file_id, self._config, self._pxmetadata_model, self._backend)

        self._dims = Dims(self._loaded_jsons, self._datadata)

        # Derive output filename. A per-language suffix is added at write time (see write_px_file).
        self._output_filename: str = self._pxmetadata_model.dataset.output_file_name or f"tab_{pxmetadata_id}"

        ##################
        self.models_by_language: dict = {}

        self._last_updated = self.get_last_updated(self._pxstatistics)

        if not self._pxmetadata_model.dataset.creation_date:
            self._creation_date = get_current_time()
        else:
            self._creation_date = convert_to_pxdate_string(
                self._pxmetadata_model.dataset.creation_date,
                self._pxmetadata_model.dataset.creation_dateformat or "%Y%m%d %H:%M",
            )

        out_model = PXFileModel()

        # loop in languages
        self._add_language_independent = True  # like AXIS_VERSION
        self._decimals: int | None = None
        self._matrix_size: int | None = None
        self._main_language = self._config.admin.valid_languages[0]
        build_start = perf_counter()
        for language in self._config.admin.valid_languages:

            self._current_lang = language
            self._contact_string = self.get_contact_string(self._pxstatistics, language)

            self.map_pxbuildconfig_to_pxfile(self._config, language, out_model)
            self.map_pxmetadata_to_pxfile(self._pxmetadata_model, out_model)
            self.map_pxstatistics_to_pxfile(self._pxstatistics, out_model)

            self.map_coded_dimensions_to_pxfile(out_model)
            self.map_measurements_to_pxfile(out_model)
            self.map_decimals_to_pxfile(out_model)
            self.map_time_dimension_to_pxfile(out_model, language)
            self.map_stub_heading_to_pxfile(out_model)
            self.map_title_to_pxfile(out_model)
            self.map_aggregallowed_to_pxfile(out_model)

            self.map_metaid_to_pxfile(out_model)
            self.map_cellnote_to_pxfile(out_model)

            if self._decimals is None:
                raise RuntimeError("Decimals were not initialized before mapping data.")
            fixdata = MapData(
                self._datadata,
                self._pxmetadata_model,
                self._config,
                self._dims,
                self._loaded_jsons,
                self._current_lang,
                self._backend,
                self._decimals,
            )
            fixdata.map_data(out_model)
            if fixdata.matrix_size is not None:
                self._matrix_size = fixdata.matrix_size

            if not self._config.admin.build_multilingual_files:
                self.models_by_language[language] = out_model
                out_model = PXFileModel()
            else:
                self._add_language_independent = False

        if self._config.admin.build_multilingual_files:
            self.models_by_language["multi"] = out_model

        self._datadata._my_datasource.close()
        self.build_seconds = perf_counter() - build_start

        self.validation_by_language: dict[str, ValidationSummary] = {
            lang: ValidationSummary.from_validate(Validate(model)) for lang, model in self.models_by_language.items()
        }

        first_model = next(iter(self.models_by_language.values()))
        self.row_count = (
            self._backend.count_rows(first_model.data.get_value()) if first_model.data.has_value() else None
        )
        self.cell_count = self.row_count

    def map_metaid_to_pxfile(self, out_model: PXFileModel) -> None:
        if self._add_language_independent:
            metaid_table: list[str] = []
            if self._pxmetadata_model.dataset.meta_id:
                metaid_table += self._pxmetadata_model.dataset.meta_id
            if self._pxstatistics.meta_id:
                metaid_table += self._pxstatistics.meta_id
            if metaid_table:
                out_model.meta_id.set("tablelevel", " ".join(metaid_table))

        lang = self._current_lang
        if self._dims.coded_dimensions:
            for n_var in self._dims.coded_dimensions:
                my_var = n_var.get_pydantic()
                if my_var.meta_id:
                    out_model.meta_id.set(" ".join(my_var.meta_id), n_var.get_label(lang), None, lang, n_var.get_code())

        contdim = self._dims.contdim
        for my_cont in self._pxmetadata_model.dataset.measurements:
            if my_cont.meta_id:
                out_model.meta_id.set(
                    " ".join(my_cont.meta_id),
                    contdim.get_label(lang),
                    my_cont.label[self._current_lang],
                    lang,
                    my_cont.code or my_cont.column_name,
                )

        if self._pxmetadata_model.dataset.time_dimension.meta_id:
            out_model.meta_id.set(
                " ".join(self._pxmetadata_model.dataset.time_dimension.meta_id),
                self._dims.time.get_label(lang),
                None,
                lang,
                "timedimension",
            )

    def map_cellnote_to_pxfile(self, out_model: PXFileModel) -> None:
        if not self._pxmetadata_model.dataset.cell_notes:
            return
        # the input is code-based , the output is dimension-order and label-based
        lang = self._current_lang

        dimension_in_order = self._dims.get_dims_in_output_order()

        for cellnote in self._pxmetadata_model.dataset.cell_notes:
            if lang not in cellnote.text:
                continue
            valuecode_by_dimensioncode = self.get_valuecode_by_dimensioncode(cellnote.attachment)
            valuetexts_for_subkey: list[str] = []
            dimcodes: list[str] = []
            for dim in dimension_in_order:
                dimcode = dim.get_code()
                dimcodes.append(dimcode)
                if dimcode in valuecode_by_dimensioncode:
                    valuecode = valuecode_by_dimensioncode[dimcode]
                    valuelabel = dim.get_valuelabel(lang, valuecode)
                    valuetexts_for_subkey.append(valuelabel)
                else:
                    valuetexts_for_subkey.append("*")

            if cellnote.is_mandatory:
                out_model.cellnotex.set(cellnote.text[lang], valuetexts_for_subkey, lang)
            else:
                out_model.cellnote.set(cellnote.text[lang], valuetexts_for_subkey, lang)

    def get_valuecode_by_dimensioncode(self, attachments: list[AttachmentItem]) -> dict[str, str]:
        my_out: dict[str, str] = {}
        for attachment in attachments:
            my_out[attachment.dimension_code] = attachment.value_code

        return my_out

    def map_aggregallowed_to_pxfile(self, out_model: PXFileModel):
        # Check if all values in the array are True
        if self._add_language_independent:
            all_boolean = all(
                isinstance(instance.aggregation_allowed, bool)
                for instance in self._pxmetadata_model.dataset.measurements
            )
            all_true = all(instance.aggregation_allowed for instance in self._pxmetadata_model.dataset.measurements)
            if all_boolean:
                out_model.aggregallowed.set(all_true)

    def map_title_to_pxfile(self, out_model: PXFileModel):
        lang = self._current_lang
        model = self._pxmetadata_model.dataset

        tmp_list = self._dims.get_dimcodes_in_output_order()
        vari_list = self._dims.get_as_lables(tmp_list, lang)

        tmp_string = ", ".join(vari_list[:-1])

        title = (
            model.base_title[lang]
            + ", "
            + self._config.admin.the_word_by[lang]
            + " "
            + tmp_string
            + " "
            + self._config.admin.the_word_and[lang]
            + " "
            + vari_list[-1]
        )

        out_model.title.set(title, self._current_lang)

    def map_stub_heading_to_pxfile(self, out_model: PXFileModel):
        lang = self._current_lang
        seen = False
        if self._dims.get_headingcodes():

            my_headings: list[str] = self._dims.get_as_lables(self._dims.get_headingcodes(), lang)
            out_model.heading.set(my_headings, lang)
            seen = True

        if self._dims.get_stubcodes():
            my_stubs: list[str] = self._dims.get_as_lables(self._dims.get_stubcodes(), lang)

            out_model.stub.set(my_stubs, lang)
            seen = True

        if not seen:
            raise ValueError("Both stub and heading are empty.")

    def map_time_dimension_to_pxfile(self, out_model: PXFileModel, language: str):
        time = self._dims.time
        lang = language

        out_model.values.set(time.get_labels(lang), time.get_label(lang), lang, time.get_code())
        out_model.codes.set(time.get_codes(), time.get_label(lang), lang, time.get_code())
        out_model.variablecode.set(time.get_code(), time.get_label(lang), lang)
        out_model.variable_type.set(time.get_variabletype(), time.get_label(lang), lang, time.get_code())

        timescale = self._pxmetadata_model.dataset.time_dimension.time_period_format
        time_dim_column_name = time.get_label(lang)

        if time._value_notes:
            for valuenote in time._value_notes:
                if valuenote.note and valuenote.value:
                    if lang not in valuenote.note.text:
                        continue
                    if valuenote.note.is_mandatory:
                        out_model.valuenotex.set(
                            valuenote.note.text[lang], time.get_label(lang), valuenote.value, lang, time.get_code()
                        )
                    else:
                        out_model.valuenote.set(
                            valuenote.note.text[lang], time.get_label(lang), valuenote.value, lang, time.get_code()
                        )

        if time._notes:
            for note in time._notes:
                if lang not in note.text:
                    continue
                if note.is_mandatory:
                    out_model.notex.set(note.text[lang], time.get_label(lang), lang, time.get_code())
                else:
                    out_model.note.set(note.text[lang], time.get_label(lang), lang, time.get_code())

        if timescale and time_dim_column_name:
            out_model.timeval.set(
                timescale=timescale,
                time_periods=time.get_codes(),
                variable=time_dim_column_name,
                lang=lang,
                code=time.get_code(),
            )

    def map_coded_dimensions_to_pxfile(self, out_model: PXFileModel):

        if self._dims.coded_dimensions:
            lang = self._current_lang
            for n_var in self._dims.coded_dimensions:

                out_model.variablecode.set(n_var.get_code(), n_var.get_label(lang), lang)
                out_model.variable_type.set(n_var.get_variabletype(), n_var.get_label(lang), lang, n_var.get_code())
                out_model.codes.set(n_var.get_codes(lang), n_var.get_label(lang), lang, n_var.get_code())
                out_model.values.set(n_var.get_labels(lang), n_var.get_label(lang), lang, n_var.get_code())

                my_var = n_var.get_pydantic()
                my_funny_var_id = n_var.get_label(lang)

                if n_var.groupings():
                    out_model.domain.set(n_var.get_domain_id(lang), my_funny_var_id, lang, n_var.get_code())

                if my_var.label_construction_option:
                    out_model.prestext.set(
                        self.LabelConstructionOptionDict[str(my_var.label_construction_option)],
                        my_funny_var_id,
                        lang,
                        n_var.get_code(),
                    )

                if n_var.get_pydantic().is_geo_variable_type:
                    label = n_var.get_geo_label(lang)
                    if label:
                        out_model.map.set(map=label, variable=n_var.get_label(lang), lang=lang, code=n_var.get_code())

                if my_var.elimination_enable:
                    if not n_var.elimination_possible():
                        out_model.elimination.set("NO", my_funny_var_id, lang, n_var.get_code())
                    else:
                        label = n_var.get_elimination_label(lang)
                        if label:
                            out_model.elimination.set(label, my_funny_var_id, lang, n_var.get_code())
                        else:
                            out_model.elimination.set("YES", my_funny_var_id, lang, n_var.get_code())

                if my_var.doublecolumn:
                    out_model.doublecolumn.set(my_var.doublecolumn, my_funny_var_id, lang, n_var.get_code())

                # Note on variable
                if my_var.notes:
                    for note in my_var.notes:
                        if lang not in note.text:
                            continue
                        if note.is_mandatory:
                            out_model.notex.set(note.text[lang], my_funny_var_id, lang, n_var.get_code())
                        else:
                            out_model.note.set(note.text[lang], my_funny_var_id, lang, n_var.get_code())

                # Note on a value in variale
                my_value_notes = n_var.get_valuenotes()
                if my_value_notes:
                    for valuecode in my_value_notes:
                        for note in my_value_notes[valuecode]:
                            if lang not in note.text:
                                continue
                            valuelabel = n_var.get_valuelabel(lang, valuecode)
                            if note.is_mandatory:
                                out_model.valuenotex.set(
                                    note.text[lang], n_var.get_label(lang), valuelabel, lang, n_var.get_code()
                                )
                            else:
                                out_model.valuenote.set(
                                    note.text[lang], n_var.get_label(lang), valuelabel, lang, n_var.get_code()
                                )

    def map_measurements_to_pxfile(self, out_model: PXFileModel):
        contdim = self._dims.contdim
        lang = self._current_lang

        # Table wide units keyword is required to avoid crash
        out_model.units.set("", None, lang, "")

        for my_cont in self._pxmetadata_model.dataset.measurements:

            my_funny_cont_id = my_cont.label[self._current_lang]

            code = contdim.get_code() if my_cont.code is None else contdim.get_code() + my_cont.code

            if isinstance(my_cont.is_seasonally_adjusted, bool):
                out_model.seasadj.set(my_cont.is_seasonally_adjusted, my_funny_cont_id, lang, code)
            if isinstance(my_cont.is_workingdays_adjusted, bool):
                out_model.dayadj.set(my_cont.is_workingdays_adjusted, my_funny_cont_id, lang, code)
            out_model.units.set(my_cont.unit_of_measure[self._current_lang], my_funny_cont_id, lang, code)
            if len(self._contact_string) > 0:
                out_model.contact.set(self._contact_string, my_funny_cont_id, lang, code)
            out_model.last_updated.set(self._last_updated, my_funny_cont_id, lang, code)

            if my_cont.reference_period and my_cont.reference_period[lang]:
                out_model.refperiod.set(my_cont.reference_period[lang], my_funny_cont_id, lang, code)

            if my_cont.base_period and my_cont.base_period[lang]:
                out_model.baseperiod.set(my_cont.base_period[self._current_lang], my_funny_cont_id, lang, code)

            if my_cont.show_decimals > 0:
                out_model.precision.set(my_cont.show_decimals, contdim.get_label(lang), my_funny_cont_id, lang, code)

            # optional with no default
            if my_cont.price_type:
                out_model.cfprices.set(self.PriceTypeDict[str(my_cont.price_type)], my_funny_cont_id, lang, code)

            # Note on a contentvalue
            if my_cont.notes:
                for note in my_cont.notes:
                    if lang not in note.text:
                        continue
                    if note.is_mandatory:
                        out_model.valuenotex.set(note.text[lang], contdim.get_label(lang), my_funny_cont_id, lang, code)
                    else:
                        out_model.valuenote.set(note.text[lang], contdim.get_label(lang), my_funny_cont_id, lang, code)

        out_model.values.set(contdim.get_labels(lang), contdim.get_label(lang), lang, contdim.get_code())
        out_model.codes.set(contdim.get_codes(), contdim.get_label(lang), lang, contdim.get_code())
        out_model.variablecode.set(contdim.get_code(), contdim.get_label(lang), lang)
        out_model.variable_type.set(contdim.get_variabletype(), contdim.get_label(lang), lang, contdim.get_code())

    def map_decimals_to_pxfile(self, out_model: PXFileModel):
        if self._add_language_independent:
            show_decimals_values = [instance.show_decimals for instance in self._pxmetadata_model.dataset.measurements]

            if self._pxmetadata_model.dataset.stored_decimals:
                self._decimals = max(self._pxmetadata_model.dataset.stored_decimals, max(show_decimals_values))
            else:
                self._decimals = max(show_decimals_values)
            out_model.decimals.set(self._decimals)
            out_model.showdecimals.set(min(show_decimals_values))

    def get_contact_string(self, in_data: PxStatistics, language: str) -> str:
        contact_string = ""

        if in_data.contacts is None:
            return contact_string

        for contact in in_data.contacts:
            if contact.raw is not None:
                contact_string += f"{contact.raw[language]}##"

        if contact_string == "":
            for contact in in_data.contacts:
                if contact.name is None:
                    return contact_string
                contact_string += f"{contact.name[language]}#{contact.phone}#{contact.email}##"

        return contact_string[:-2]

    def get_last_updated(self, in_model: PxStatistics) -> str:
        last_updated_date = ""
        if in_model.upcoming_releases is None:
            return last_updated_date

        if len(in_model.upcoming_releases) < 1:
            return last_updated_date

        last_updated_date = in_model.upcoming_releases[0]

        formatted_string = convert_to_pxdate_string(
            last_updated_date, self._pxstatistics.upcoming_releases_dateformat or "%Y%m%d %H:%M"
        )

        return formatted_string

    def get_next_update(self, in_model: PxStatistics) -> str:
        last_updated_date = ""
        if in_model.upcoming_releases is None:
            return last_updated_date

        if len(in_model.upcoming_releases) < 2:
            return last_updated_date

        last_updated_date = in_model.upcoming_releases[1]

        formatted_string = convert_to_pxdate_string(
            last_updated_date, self._pxstatistics.upcoming_releases_dateformat or "%Y%m%d %H:%M"
        )

        return formatted_string

    def map_pxstatistics_to_pxfile(self, in_model: PxStatistics, out_model: PXFileModel):
        lang = self._current_lang

        out_model.subject_area.set(in_model.subject_text[lang], lang)
        if self._add_language_independent:
            out_model.subject_code.set(in_model.subject_code)

            next_update = self.get_next_update(self._pxstatistics)
            if next_update:
                out_model.next_update.set(next_update)

        # out_model.update_frequency.set() Hmm is not listed as language dependent in pdf

    def map_pxmetadata_to_pxfile(self, in_model: PxMetadata, out_model: PXFileModel):
        lang = self._current_lang
        if self._add_language_independent:
            out_model.tableid.set(in_model.dataset.table_id)

            if self._pxmetadata_model.dataset.matrix is None:
                matrix = f"tab_{self._pxmetadata_id}"
            else:
                matrix = self._pxmetadata_model.dataset.matrix
            out_model.matrix.set(matrix)

            if in_model.dataset.official_statistics:
                out_model.official_statistics.set(in_model.dataset.official_statistics)
            if in_model.dataset.copyright:
                out_model.copyright.set(in_model.dataset.copyright)
            if not self._config.admin.skip_creation_date:
                out_model.creation_date.set(self._creation_date)
            if in_model.dataset.first_published:
                out_model.first_published.set(in_model.dataset.first_published)

            # The SYNONYMS keyword is language independent. So, all langs go into one for multilingual_files.
            if in_model.dataset.search_keywords:
                temp_tags: list[str] = []
                if self._config.admin.build_multilingual_files:
                    for language in self._config.admin.valid_languages:
                        temp_tags += in_model.dataset.search_keywords[language]
                else:
                    temp_tags = in_model.dataset.search_keywords[lang]
                if temp_tags:
                    out_model.synonyms.set(" ".join(temp_tags))

        if in_model.dataset.description and in_model.dataset.description[lang]:
            out_model.description.set(str(in_model.dataset.description[lang]), lang)

        out_model.contents.set(in_model.dataset.base_title[lang], lang)
        if in_model.dataset.notes:
            for note in in_model.dataset.notes:
                if lang not in note.text:
                    continue
                if note.is_mandatory:
                    out_model.notex.set(note.text[lang], None, lang, "")
                else:
                    out_model.note.set(note.text[lang], None, lang, "")

    def map_pxbuildconfig_to_pxfile(self, in_config: PxbuildConfig, current_lang: str, out_model: PXFileModel):
        if self._add_language_independent:
            out_model.language.set(current_lang)
            if in_config.admin.build_multilingual_files:
                out_model.languages.set(in_config.admin.valid_languages)
            else:
                # Single-language file: LANGUAGES must still be present, listing only this file's language.
                out_model.languages.set([current_lang])
            out_model.axis_version.set(str(in_config.axis_version))
            if in_config.charset is not None:
                out_model.charset.set(str(in_config.charset))
            out_model.codepage.set(str(in_config.code_page))
            if in_config.description_default is not None:
                out_model.descriptiondefault.set(in_config.description_default)

        contvariable = in_config.contvariable
        if contvariable is None:
            raise ValueError("contvariable must be configured.")
        out_model.contvariable.set(str(contvariable[current_lang]), current_lang)

        if in_config.datasymbol1 and in_config.datasymbol1[self._current_lang]:
            out_model.datasymbol1.set(str(in_config.datasymbol1[self._current_lang]), self._current_lang)
        if in_config.datasymbol2 and in_config.datasymbol2[self._current_lang]:
            out_model.datasymbol2.set(str(in_config.datasymbol2[self._current_lang]), self._current_lang)
        if in_config.datasymbol3 and in_config.datasymbol3[self._current_lang]:
            out_model.datasymbol3.set(str(in_config.datasymbol3[self._current_lang]), self._current_lang)
        if in_config.datasymbol4 and in_config.datasymbol4[self._current_lang]:
            out_model.datasymbol4.set(str(in_config.datasymbol4[self._current_lang]), self._current_lang)
        if in_config.datasymbol5 and in_config.datasymbol5[self._current_lang]:
            out_model.datasymbol5.set(str(in_config.datasymbol5[self._current_lang]), self._current_lang)
        if in_config.datasymbol6 and in_config.datasymbol6[self._current_lang]:
            out_model.datasymbol6.set(str(in_config.datasymbol6[self._current_lang]), self._current_lang)
        if in_config.datasymbol_nil and in_config.datasymbol_nil[self._current_lang]:
            out_model.datasymbolnil.set(str(in_config.datasymbol_nil[self._current_lang]), self._current_lang)
        if in_config.datasymbol_sum and in_config.datasymbol_sum[self._current_lang]:
            out_model.datasymbolsum.set(str(in_config.datasymbol_sum[self._current_lang]), self._current_lang)

        source = in_config.source
        if source is None:
            raise ValueError("source must be configured.")
        out_model.source.set(source[self._current_lang], self._current_lang)


def convert_to_pxdate_string(date_string: str, date_format: str) -> str:
    dtm_date = datetime.strptime(date_string, date_format).replace(tzinfo=timezone.utc)
    px_date_string = dtm_date.strftime("%Y%m%d %H:%M")

    return px_date_string


def get_current_time() -> str:
    """
    Returns the current time as a string in the format CCYYMMDD hh:mm
    """
    from datetime import datetime

    return datetime.now(timezone.utc).strftime("%Y%m%d %H:%M")


def write_output(
    pxmetadata_id: str,
    px_folder_format: str,
    out_model: PXFileModel,
    output_filename: str,
    backend: "IBackendMethods",
    main_language: str,
    encoding: str | None = None,
) -> str:
    out_folder = px_folder_format.format(id=pxmetadata_id)
    Path(out_folder).mkdir(parents=True, exist_ok=True)
    out_file = f"{out_folder}/{output_filename}.px"

    if encoding is None:
        encoding = "cp1252"
    try:
        "".encode(encoding)
    except LookupError:
        logger.warning(f"Config.codePage '{encoding}' is not valid encoding for printing. Defaulting to 'cp1252'")
        encoding = "cp1252"

    if "utf" in encoding.lower() and "-sig" not in encoding.lower():
        encoding = encoding + "-sig"

    out_model.write_to_file(out_file, encoding=encoding, backend=backend, main_language=main_language)

    logger.info(f"File written to: {out_file}")

    return out_file


def build_px_model(
    pxmetadata_id: str, config_file: str | dict, backend: str = "pandas", debug: bool = False
) -> PxBuildModel:
    """Build the in-memory PXFileModel(s) for a pxmetadata id. No file I/O happens here.

    Validation runs automatically as part of the build; see the returned model's
    ``validation_by_language``/``is_valid`` for the results.
    """
    builder = _PxModelBuilder(pxmetadata_id, config_file, backend, debug)
    statistics = PxBuildStatistics(
        languages=list(builder.models_by_language.keys()),
        decimals=builder._decimals,
        matrix_size=builder._matrix_size,
        row_count=builder.row_count,
        cell_count=builder.cell_count,
        build_seconds=builder.build_seconds,
    )
    return PxBuildModel(
        pxmetadata_id=pxmetadata_id,
        models_by_language=builder.models_by_language,
        config=builder._config,
        dims=builder._dims,
        pxmetadata=builder._pxmetadata_model,
        output_filename=builder._output_filename,
        backend=builder._backend,
        main_language=builder._main_language,
        statistics=statistics,
        validation_by_language=builder.validation_by_language,
    )


def write_px_file(model: PxBuildModel) -> list[str]:
    """Write a previously built PxBuildModel to disk. Returns the written .px file path(s).

    Also records the written paths and elapsed write time onto ``model.statistics``.
    """
    if not model.is_valid:
        raise PxBuildValidationError(model.validation_by_language)

    write_start = perf_counter()
    written_files: list[str] = []
    px_folder_format = model.config.admin.output_destination.px_folder_format
    if px_folder_format is None:
        raise ValueError("pxFolderFormat must be configured before writing PX files.")
    for lang, out_model in model.models_by_language.items():
        # Single-language files get a per-language suffix so they don't overwrite each other,
        # and are rendered with that language as "main" so keywords omit the [lang] tag.
        is_multi = lang == "multi"
        out_file = write_output(
            model.pxmetadata_id,
            px_folder_format,
            out_model,
            model.output_filename if is_multi else f"{model.output_filename}_{lang}",
            model.backend,
            model.main_language if is_multi else lang,
            model.config.code_page,
        )
        written_files.append(out_file)

    if model.config.admin.make_support_files:
        support = SupportFiles(model.pxmetadata, model.config, model.dims, model.pxmetadata_id)
        support.make_vs_file()

    model.statistics.output_files = written_files
    model.statistics.write_seconds = perf_counter() - write_start

    return written_files


def build_px_file(
    pxmetadata_id: str, config_file: str | dict, backend: str = "pandas", debug: bool = False
) -> PxBuildModel:
    """Convenience wrapper: build the in-memory model(s) and write them to disk in one call.

    Returns the built :class:`PxBuildModel`, whose ``.statistics.output_files`` holds
    the written .px file path(s).
    """
    model = build_px_model(pxmetadata_id, config_file, backend, debug)
    write_px_file(model)
    return model
