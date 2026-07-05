# droning-simulation-infra

Инфраструктурный контур для проверки симуляционного стека дронов в Docker.

## Назначение

Репозиторий фиксирует воспроизводимую базу для локальных и CI-проверок:

- ROS 2 Jazzy на Ubuntu 24.04;
- Gazebo через ROS-Gazebo;
- MAVROS и MAVLink;
- OpenCV для Python через системные пакеты Ubuntu;
- rosbag2 с хранилищем MCAP;
- базовый smoke-контроль ArduPilot SITL-образа.

GPU не является обязательным требованием для текущего контура.

## Требования

- WSL2 или Linux;
- Docker;
- `make`;
- `python3`;
- `jq`.

Для локальной проверки инструментов:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

## Основные команды

```bash
make validate
make docker-build
make docker-smoke
make docker-update-check
make security-scan
make ci
```

`make ci` выполняет полный локальный прогон: проверку контрактов, сборку образа, smoke-проверки,
сверку зафиксированных пакетов и SARIF-отчет Trivy.

## Структура

```txt
.devcontainer/                       Dev Container
.github/                             CI, update-check, Dependabot
contracts/infra/stack.schema.json    JSON Schema контракта стека
infra/docker/                        Dockerfile симуляционного образа
infra/stack/simulation-stack.json    зафиксированный состав стека
Makefile                             единая точка входа для локальных и CI-проверок
requirements-dev.txt                 инструменты валидации
```

## Артефакты

Локальные отчеты пишутся в `artifacts/` и не попадают в Git.
