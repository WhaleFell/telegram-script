#include <iostream>
#include <ctime>
#include <random>
#include <sstream>
#include <Windows.h>

std::string generateUUID() {
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<int> dis(0, 15);
    std::stringstream ss;
    for (int i = 0; i < 32; i++) {
        int randomDigit = dis(gen);
        if (i == 8 || i == 12 || i == 16 || i == 20) {
            ss << "-";
        }
        ss << std::hex << std::uppercase << randomDigit;
    }
    return ss.str();
}

std::string getCurrentTime() {
    std::time_t now = std::time(nullptr);
    char buffer[20];
    std::strftime(buffer, sizeof(buffer), "%Y-%m-%d %H:%M:%S", std::localtime(&now));
    return buffer;
}

int main() {
    std::string uuid = generateUUID();
    std::string currentTime = getCurrentTime();
    std::string message = "文件已经损坏了\n" + uuid + "\n" + currentTime;

    HWND hwnd = GetConsoleWindow();
    ShowWindow(hwnd, SW_HIDE);

    MessageBox(NULL, message.c_str(), "Error", MB_OK);

    return 0;
}
