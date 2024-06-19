# VM Cloud Manager

## Описание
Проект "VM Cloud Manager" предназначен для управления виртуальными машинами 
в облаке Yandex Cloud. Он позволяет автоматически останавливать ВМ, срок действия которых истек. 
Скрипт проверяет все ВМ во всех папках организации и останавливает те из них, которые имеют 
метку `expired_date`, если их срок действия истек и они находятся в состоянии работы.

## Установка и запуск

1. Клонируйте репозиторий:
```bash
git clone https://github.com/Searchforsomething/vm-cloud-manager.git
cd vm-cloud-management
```
2. Если у вас не установлен docker, установите его:
```bash
sudo apt install docker.io
```
3. Создайте файл .env и запишите в него свои данные:
```
OAUTH_TOKEN=<your_oauth_token>
ORGANIZATION_ID=<your_organization_id>
```
4. Для сборки запустите в каталоге проекта:
```bash
sudo docker build -t vm-cloud-management .
```
5. Для запуска нужно выполнить в терминале команду:
```bash
sudo docker run --env-file .env vm-cloud-manager
```
