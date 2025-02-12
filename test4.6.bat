start cmd /k "python LocalController.py --config .\config\topo5as32sw_test4.6\asConfig1.json"
start cmd /k "python LocalController.py --config .\config\topo5as32sw_test4.6\asConfig2.json"
start cmd /k "python LocalController.py --config .\config\topo5as32sw_test4.6\asConfig3.json"
start cmd /k "python LocalController.py --config .\config\topo5as32sw_test4.6\asConfig4.json"
start cmd /k "python LocalController.py --config .\config\topo5as32sw_test4.6\asConfig5.json"
sleep 0.5
start cmd /k "python FedController.py --config .\config\topo5as32sw_test4.6\globalConfig.json"