class Description:
    def __init__(self) -> None:
        self._section = "[Descr]"
        self._key_value_rows: list[dict[str, str]] = []

    def set(self, vskey: str, vsvalue: str):

        my_dict = {"key": vskey, "val": vsvalue}
        self._key_value_rows.append(my_dict)

    def __str__(self):
        out_str = f"{self._section}\n"

        for my_dict in self._key_value_rows:
            out_str = out_str + f"{my_dict['key']}={my_dict['val']} \n"
        return out_str
