# pip install --upgrade --pre uiautomator2
import os
import uiautomation as auto
import subprocess


class uiautoTG():
    def __init__(self):
        super().__init__()
        auto.uiautomation.DEBUG_SEARCH_TIME = True
        auto.uiautomation.SetGlobalSearchTimeout(2)  # 设置全局搜索超时时间
        self.tgWindow = auto.WindowControl(
            searchDepth=1, Name='Telegram', desc='TG窗口')  # 计算器窗口
        if not self.tgWindow.Exists(0, 0):
            subprocess.Popen(r"E:\TEMP\Telegram\telegram.exe")  # 设置窗口前置
            self.tgWindow = auto.WindowControl(
                searchDepth=1, Name='Telegram', desc='TG窗口')
        self.tgWindow.SetActive()  # 激活窗口
        self.tgWindow.SetTopmost(True)  # 设置为顶层

    def gotoRegister(self):
        pass

    def gotoScientific(self):
        self.tgWindow.ButtonControl(
            AutomationId='TogglePaneButton', desc='打开导航').Click(waitTime=0.01)
        self.tgWindow.ListItemControl(
            AutomationId='Scientific', desc='选择科学计算器').Click(waitTime=0.01)
        clearButton = self.tgWindow.ButtonControl(
            AutomationId='clearEntryButton', desc='点击CE清空输入')
        if clearButton.Exists(0, 0):
            clearButton.Click(waitTime=0)
        else:
            self.tgWindow.ButtonControl(
                AutomationId='clearButton', desc='点击C清空输入').Click(waitTime=0.01)

    # def getKeyControl(self):
    #     automationId2key = {'num0Button': '0', 'num1Button': '1', 'num2Button': '2', 'num3Button': '3', 'num4Button': '4', 'num5Button': '5', 'num6Button': '6', 'num7Button': '7', 'num8Button': '8', 'num9Button': '9',
    #                         'decimalSeparatorButton': '.', 'plusButton': '+', 'minusButton': '-', 'multiplyButton': '*', 'divideButton': '/', 'equalButton': '=', 'openParenthesisButton': '(', 'closeParenthesisButton': ')'}
    #     calckeys = self.tgWindow.GroupControl(ClassName='LandmarkTarget')
    #     keyControl = {}
    #     for control, depth in auto.WalkControl(calckeys, maxDepth=3):
    #         if control.AutomationId in automationId2key:
    #             keyControl[automationId2key[control.AutomationId]] = control
    #     return keyControl

    # def calculate(self, expression, keyControl):
    #     expression = ''.join(expression.split())
    #     if not expression.endswith('='):
    #         expression += '='
    #         for char in expression:
    #             keyControl[char].Click(waitTime=0)
    #     self.tgWindow.SendKeys('{Ctrl}c', waitTime=0.1)
    #     return auto.GetClipboardText()

    # def calc_demo(self):
    #     self.gotoScientific()  # 选择科学计算器
    #     keyControl = self.getKeyControl()  # 获取按键控件
    #     result = self.calculate('(1 + 2 - 3) * 4 / 5.6 - 7', keyControl)
    #     print('(1 + 2 - 3) * 4 / 5.6 - 7 =', result)
    #     self.tgWindow.CaptureToImage(
    #         'calc.png', x=7, y=0, width=-14, height=-7)  # 截图
    #     self.tgWindow.GetWindowPattern().Close()  # 关闭计算机


if __name__ == "__main__":
    ui = uiautoTG()
