## Минуточку внимания!
Поскольку администрация ВКонтакте решила 15 февраля [закрыть доступ к API сообщений](https://vk.com/dev/messages_api), данный скрипт рискует потерять часть своего функционала. Пока идёт процесс прохождения модерации. Остаётся надеяться на лучшее :з

*UPD: уже была рассылка с напоминанием о возможности пройти модерацию, однако пока никаких новостей с конца января - "Ваш вопрос рассматривается."*

*UPD2: всё, API сообщений прикрыли, а ответа так и нет. Из scope исключил права на доступ к сообщениям - скрипт продолжит работу, но сообщения и всё связанное с ними ничего сохранить нельзя ¯\\\_(ツ)_/¯*

*UPD3: временный костыль для доступа к сообщениям - получение токена идёт с app_id VKontakte for Android. При успехе сам токен записывается в файл `token`, и авторизовываться лучше с помощью него ([\*тык\*](https://github.com/hikiko4ern/vk_dump#%D0%B0%D0%B2%D1%82%D0%BE%D1%80%D0%B8%D0%B7%D0%B0%D1%86%D0%B8%D1%8F)), ибо повторная авторизация по логину-паролю будет запрашивать новый токен и т.д.*

## Установка зависимостей
```
pip3 install -r requirements.txt
```

Если Вы используете Windows ниже 10 версии, необходимо дополнительно установить пакет `colorama`:
```
pip3 install colorama
```

## CLI
Все доступные аргументы можно посмотреть при запуске с `--help`.

Для сохранения нескольких типов данных за один вызов необходимо указывать каждый тип отдельным аргументом `dump`.
Например, для сохранения фото и видео надо запускать `dump.py --dump photos --dump video`.

## Конфиг модуля vk_api
Поскольку в конфиге хранится `access_token`, получаемый с `offline` правом, позволяющим пройти аутентификацию с любого IP без необходимости ввода кода двухфакторной аутентификации, по умолчанию конфиг будет записываться в память.

Однако, в таком случае, при каждой попытке входа будет запрошен новый код двухфакторой аутентификации, если она включена. Если Вы уверены в безопасности данных, хранимых в конфиге, в настройках можете отключить принудительное сохранение в память через настройки.

## Авторизация
Возможны два способа аутентификации - с помощью пары логин-пароль или токена.

Для входа по токену необходимо передать аргумент `token` при запуске:
```
python3 dump.py --token your_token_here
```

## Мультипоточная загрузка
Количество процессов, создаваемых для загрузки, по умолчанию равняется `4*потоки`.

При загрузке видео - числу, заданному в настройках, но не больше количества потоков.
Такое ограничение введено ввиду отсутствия смысла в спаме лишними процессами при загрузке больших по размеру видео (однако лимит всё же убирается через настройки).

## Поддерживаемые для сохранения данные
- [x] Фото
- [x] Видео
- [x] Документы
- [x] Диалоги (txt) и вложения (фото, видео, документы, голосовые)
- [x] Вложения понравившихся постов (фото, видео, документы)
- [x] Понравившиеся фотографии и видео
- [ ] прочее, прочее, прочее ;)

## Исключение диалогов из сохранения
Для исключения диалога из списка сохраняемых необходимо дописать его id в конфиге `settings.ini`.
ID необходимо перечислять через запятую. Получить его можно, например, открыв диалог в разделе сообщений, тогда в URL вида `https://vk.com/im?sel=100` идентификатором будет являться кусок, идущий после `sel=`.

Пример с пропуском диалога с ID `100` и беседы `c60`:
```ini
[EXCLUDED_DIALOGS]
id = 100,c60
```

## "Дозапись" новых сообщений вместо перезаписывания
Можно включить в настройках, тогда при кэшировании будут получены не все сообщения, а только с ID больше сохранённого (последняя строка в файле). После включения опции первое кэширование будет полным, в последующие разы - только "новые" сообщения.

## F.A.Q.
**Q: Ошибка vk_api.exceptions.AccessDenied: You don't have permissions to browse user's...**\
**A:** Попробуйте удалить файл `vk_config.v2.json` и переавторизироваться.

**Q: Ошибка RegexNotFoundError('Unable to extract %s' % _name)**\
**A:** Обновите `youtube_dl`: `pip3 install --upgrade youtube_dl`.
