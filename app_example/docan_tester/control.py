from task import Task
class Controller:
    ui: object
    task: Task
    cnt: int = 0
    def init(self, ui):
        self.ui = ui
        # TODO 组件初始化 赋值操作
        self.task = Task(self)
        
    def show_edit(self,evt):
        self.cnt += 1
    
    def set_spinbox(self,num):
        self.ui.spinbox.set(num)
