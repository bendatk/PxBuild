class Commons:
    @classmethod
    def set_main_language(cls, lang: str):
        cls.main_language = lang
    
    @staticmethod
    def get_main_language() -> str:
        return Commons.main_language
    
    @classmethod
    def set_decimals(cls, decimals: int):
        cls.decimals = decimals
    
    @staticmethod
    def get_decimals() -> int:
        return Commons.decimals
    
    @classmethod
    def set_matrix_size(cls, matrix_size: int):
        cls.matrix_size = matrix_size

    @staticmethod
    def get_matrix_size() -> int:
        return Commons.matrix_size