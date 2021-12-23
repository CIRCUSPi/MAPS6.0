# MAPS6.0 WiFi and NB-IoT Version
此版本依照 [MAPS6_NTU_Special](https://github.com/SCWhite/MAPS6_NTU_Special) 功能大幅重構

## 修改內容
- 新增 NBIoT 模組 SIM7000 Library
- 新增 Simcom 專用 MQTT Library （適用SIM7000、SIM800、SIM7020、AM7020）
- 新增下位機 Mega2560 Library（讀取各感測器資料）
- 移除分貝計相關功能
- 修改主程式流程
- 更新 Raspbian 版本(2021-10-30 armhf-full)
- 與下位機 Mega2560 通訊使用 Hardware Serial(ttyAMA0)
- OLED 加入 NB-IoT 訊號數值（僅在使用NBIoT通訊時顯示，訊號範圍0~31，建議放置在訊號數值大於16的位置）
- OLED 加入顯示網路連接方式（W(Wifi)/N(NBIoT)/-(無網路)）
- 自動判斷通訊方式，優先權 WiFi >> NBIoT
- 連網後自動校正 RTC

## 注意事項
- 此版本只適用MAPS6 Firmware version 1.22版以上



