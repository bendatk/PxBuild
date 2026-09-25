from pxbuild.models.output.pxfile.util._px_keytypes import (
    _KeytypeCodes,
    _KeytypeValuesLangMulti,
    _KeytypeVariableValueLangMulti,
    _KeytypeVariableLangMulti,
    _KeytypeLang,
    _KeytypeVariableLang,
    _KeytypeContentLang,
    _KeytypeVariableValueLang,
)


def test_keytypes_never_equal_a_plain_string():
    my_str = "no"

    assert _KeytypeLang("no") != my_str
    assert _KeytypeVariableLang("region", "no") != my_str
    assert _KeytypeContentLang("region", "no") != my_str
    assert _KeytypeVariableValueLang("region", "oslo", "no") != my_str
    assert _KeytypeVariableLangMulti("region", "no", 1) != my_str
    assert _KeytypeVariableValueLangMulti("region", "oslo", "no", 1) != my_str
    assert _KeytypeCodes(["kongsvinger", "oslo"]) != my_str


def test_keytypevariablelang_reset_lang_none_to_keeps_existing_lang():
    my_key = _KeytypeVariableLang("region", "no")
    reset_key = my_key.reset_lang_none_to("sv")
    # lang was already set, so reset_lang_none_to is a no-op.
    assert reset_key.lang == "no"


def test_keytypecontentlang_to_str_message_mentions_the_variable():
    my_key = _KeytypeContentLang("region", "no")
    assert "region" in my_key.to_str_message()


def test_keytypevalueslangmulti_equality_and_hash():
    my_key = _KeytypeValuesLangMulti(["kongsvinger", "oslo"], "no", 1)
    assert my_key != "astring"

    my_key2 = _KeytypeValuesLangMulti(["kongsvinger", "oslo"], "no", 1)
    assert my_key == my_key2
    assert hash(my_key) == hash(my_key2)

    my_key3 = _KeytypeValuesLangMulti(["kongsvinger", "Oslo"], "no", 1)
    assert my_key != my_key3


def test_keytypevalueslangmulti_reset_lang_none_to_sets_lang():
    my_key = _KeytypeValuesLangMulti(["kongsvinger", "Oslo"], None, 1)
    reset_key = my_key.reset_lang_none_to("sv")

    assert isinstance(reset_key, _KeytypeValuesLangMulti)
    assert reset_key.lang == "sv"


def test_keytypevalueslangmulti_is_a_keytypelang_subclass():
    my_key = _KeytypeValuesLangMulti(["kongsvinger", "oslo"], "no", 1)
    my_key_lang = _KeytypeLang("no")

    assert isinstance(my_key, _KeytypeLang)
    assert type(my_key) is not type(my_key_lang)


def test_keytypevalueslangmulti_not_equal_to_keytypelang():
    my_key = _KeytypeValuesLangMulti(["kongsvinger", "oslo"], "no", 1)
    my_key_lang = _KeytypeLang("no")

    assert my_key != my_key_lang
    assert my_key_lang != my_key


def test_keytypelang_equal_when_same_lang():
    assert _KeytypeLang("no") == _KeytypeLang("no")
