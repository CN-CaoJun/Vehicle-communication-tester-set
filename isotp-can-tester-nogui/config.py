import json

class Config:
    def load_case(self, config_file):
        try:
            with open(config_file, "r") as fd:
                self.config = json.load(fd)
                return self.config
        except:
            print("test case file parse failed")
            return None
    def find_case(self, req):
        for case in self.config:
            if case["req"].upper() == req:
                return case["res"]
        return None
