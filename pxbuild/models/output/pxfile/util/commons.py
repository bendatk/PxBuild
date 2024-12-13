class Commons:
    @classmethod
    def set_main_language(cls, lang: str):
        cls.main_language = lang
    
    @staticmethod
    def get_main_language() -> str:
<<<<<<< HEAD
        return Commons.main_language
    
    @classmethod
    def set_decimals(cls, decimals: int):
        cls.decimals = decimals
    
    @staticmethod
    def get_decimals() -> int:
        return Commons.decimals
=======
        return Commons.main_language
>>>>>>> c5a8254 (Language in output: omit printing main langauge)
