import TUI.Models.TUIModel
import TUI.TUIMenu.AboutWindow
import TUI.TUIMenu.ConnectWindow
import TUI.TUIMenu.DownloadsWindow
import TUI.TUIMenu.LogWindow
import TUI.TUIMenu.PreferencesWindow
import TUI.TUIMenu.PythonWindow
import TUI.TUIMenu.UsersWindow
import TUI.Misc.MessageWindow
import TUI.TCC.StatusWdg.StatusWindow

def loadAll():
    tuiModel = TUI.Models.TUIModel.Model()
    tlSet = tuiModel.tlSet
    TUI.TUIMenu.AboutWindow.addWindow(tlSet)
    TUI.TUIMenu.ConnectWindow.addWindow(tlSet)
    TUI.TUIMenu.DownloadsWindow.addWindow(tlSet)
    TUI.TUIMenu.LogWindow.addWindow(tlSet)
    TUI.TUIMenu.PreferencesWindow.addWindow(tlSet)
    TUI.TUIMenu.PythonWindow.addWindow(tlSet)
    TUI.TUIMenu.UsersWindow.addWindow(tlSet)
    TUI.Misc.MessageWindow.addWindow(tlSet)
    TUI.TCC.StatusWdg.StatusWindow.addWindow(tlSet)
