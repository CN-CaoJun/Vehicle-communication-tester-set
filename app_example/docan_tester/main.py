from ui import Win
from control import Controller

app = Win(Controller())
if __name__ == "__main__":
    # 启动
    app.mainloop()