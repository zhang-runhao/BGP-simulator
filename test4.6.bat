start cmd /k "python LocalController.py --config .\config\5as32sw_0220\asConfig1.json"
start cmd /k "python LocalController.py --config .\config\5as32sw_0220\asConfig2.json"
start cmd /k "python LocalController.py --config .\config\5as32sw_0220\asConfig3.json"
start cmd /k "python LocalController.py --config .\config\5as32sw_0220\asConfig4.json"
start cmd /k "python LocalController.py --config .\config\5as32sw_0220\asConfig5.json"
sleep 0.5
start cmd /k "python FedController.py --config .\config\5as32sw_0220\globalConfig.json"