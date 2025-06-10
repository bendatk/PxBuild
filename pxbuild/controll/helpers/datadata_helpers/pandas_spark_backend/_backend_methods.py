from abc import ABC, abstractmethod
from ._fileio import IFileIO
from ._transforms import ITransforms
from ._validation import IValidation
from ._utility import IUtility
from ._fileio import IFileIO

class IBackendMethods(IFileIO, ITransforms, IValidation, IUtility, ABC):

    @property
    @abstractmethod
    def backend_name(self) -> str:
        pass
