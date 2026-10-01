from abc import ABC, abstractmethod

from ._fileio import IFileIO
from ._transforms import ITransforms
from ._utility import IUtility
from ._validation import IValidation


class IBackendMethods(IFileIO, ITransforms, IValidation, IUtility, ABC):
    @property
    @abstractmethod
    def backend_name(self) -> str:
        pass
