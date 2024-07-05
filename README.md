# Document Generator

## Опис

Сервіс створений для генерації `.docx` документів за здалегідь визначеним шаблоном. Список підтримуваних можливостей генератора:

- Підстановка тексту в рядок
- Створення параграфів
- Вставка зображень
- Вставка формул
- Створення таблиць
- Створення списків
- Генерація QR Code

## Системні вимоги

**Операційна система:**

- Linux
- Windows
- MacOS (протестовано на Apple Silicon)

**Процесор:**

- x64
- ARM (Apple Silicon)

**Оперативна памʼять:**

- мінімум 1гб

**Розмір сховища:**

- мінімум 1гб, також необхідно передбачити обʼєм для зберігання .docx шаблонів

## Архітектура

### Структура проєкту

```
├── Dockerfile
├── README.md
├── ROADMAP.md
├── app
│   ├── MML2OMML.XSL    // файл для конвертацій формул
│   ├── api             // роути застосунку
│   ├── core            // підключення, логування, конфігурація
│   ├── internal
│   │   ├── docx        // генератор документів
│   │   ├── storage     // сховище даних
│   │   ├── template    // шаблони, версії шаблонів
│   │   ├── mixin.py
│   │   └── webclient.py
│   └── main.py
├── deploy.sh
├── docker-compose.yml
├── poetry.lock
└── pyproject.toml

```

### Конфігурація

Опис конфігураційних значень:

`API_PREFIX` (string)

- **Опис:** Визначає базовий префікс API.
- **Значення за замовчуванням:** `api/v1`

`BACKEND_CORS_ORIGINS` (list[string])

- **Опис:** список дозволених CORS адресів.
- **Значення за замовчуванням:** `[]`

`LOCAL_STORAGE_TEMPLATE_PATH` (string)

- **Опис:** шлях збереження шаблонів для типу сховища `LOCAL`.
- **Значення за замовчуванням:** `'.templates'`

`LOCAL_STORAGE_TMP_PATH` (string)

- **Опис:** шлях до директорії з тимчасовими файлами.
- **Значення за замовчуванням:** `'.tmp'`

Приклад конфігурацій для сервісу:

```
API_PREFIX=/api/v1
BACKEND_CORS_ORIGINS=
LOCAL_STORAGE_TEMPLATE_PATH=templates
LOCAL_STORAGE_TMP_PATH=tmp
```

## Опис API

Swagger документація доступна за шляхом `{host}/docs`. Всі функціональні маршрути починаються з префіксу `/api/v1`.

**Опис полів JSON для генерації документів:**

`{VARNAME}` (string | bool | array)

**Опис:** довільний ключ `JSON`. Це значення буде інтерпретуватися шаблонізатором буквально. Наприклад, якщо необхідно додати в документ текстове значення, в шаблон заноситься змінна `{{SOME_TEXT}}`, і в `JSON` повинен бути ключ під назвою `SOME_TEXT` з текстовим значенням, що підставиться в цю змінну під час генерації документу. Те саме стосується формування таблиць та списків, але в такому разі потрібно передати не тестову інформацію, а масив значень, які будуть ітеруватися шаблонізатором.

Якщо в тексті наявні наступні символи: `[>, <, ", &]`, то таку змінну в шаблоні необхідно задати зі спеціальним фільтром. Наприклад, якщо є змінна `COMPARISON`, що містить рядок `2 < 5`, то таку змінну треба задати наступним чином: `{{ COMPARISON|e }}` замість `{{ COMPARISON }}`.

`IMG|{VARNAME}` (`InlineImage`)

**Опис:** ключ, що відповідає за вставку зображення в документ. Принцип схожий на попередній випадок, але з додаванням префіксу `IMG`. Нехай в шаблоні знаходиться змінна `{{SOME_IMAGE}}`, тоді в `JSON` треба передати ключ `IMG|SOME_IMAGE` зі значенням URL зображення, яке треба підставити.

Модель даних `InlineImage`:

```json
{
  "source": "http://...", // string, URL зображення
  "width": 5, // OPTIONAL int, ширина зображення в мм
  "height": 7 // OPTIONAL int, висота зображення в мм
}
```

`MATH|{VARNAME}` (`LatexFormula`)

**Опис:** Поле, що відповідає за вставку формули в документ. Префікс `MATH` визначає, що дані треба обробити як математичну формулу. Значення очікується в нотації `LaTeX`.

Модель даних `LatexFormula`:

```json
{
  "formula": "x^n + y^n = z^n"
}
```

`QR|{VARNAME}` (`QrCode`)

**Опис:** Поле, що відповідає за вставку QR Code. Префікс `QR` визначає, що дані треба обробити як QR Code.

Модель даних `QrCode`:

```json
{
  "data": "some coded data",
  "width": 5, // OPTIONAL int, ширина зображення в мм
  "height": 7 // OPTIONAL int, висота зображення в мм
}
```

**Приклад JSON для генерації документу:**

```json
{
  "DOC_TITLE": "My awesome document",
  "COL_ROWS": [
    {
      "COL1": "col11",
      "COL2": "col12",
      "COL3": "col13",
      "IMG|COL4": {
        "source": "https://logos-world.net/wp-content/uploads/2021/10/Python-Logo.png",
        "width": 5,
        "height": 5
      }
    },
    {
      "COL1": "col21",
      "COL2": "col22",
      "COL3": "col23",
      "IMG|COL4": {
        "source": "https://logos-world.net/wp-content/uploads/2021/10/Python-Logo.png",
        "width": 5,
        "height": 5
      }
    }
  ],
  "HEADER": "some header",
  "HEADER_MIDDLER": "middle header",
  "CONDITIONAL_P": true,
  "P_TEXT": "some paragraph if true",
  "QR|YOUTUBE": {
    "data": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "width": 15,
    "height": 15
  },
  "MATH|FORMULA654": {
    "formula": "\\sum_{i=1}^{10}{\\frac{\\sigma_{zp,i}}{E_i} kN"
  },
  "IMG|IMAGE123": {
    "source": "https://logos-world.net/wp-content/uploads/2021/10/Python-Logo.png",
    "width": 15,
    "height": 15
  }
}
```

На вихід повертається згенерований `.docx` документ.

## Розгортання

### Локальне розгортання

**Створення віртуального середовища:**

```bash
poetry install --no-root
```

**Запуск сервісу:**

```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port 4444
```

### Docker

Внутрішній порт сервісу в Docker Container: `80`.

**Збірка Docker Image**:

```bash
docker build -t document-generator .
```

**Запуск контейнеру**:

Запуск відбувається через підняття `docker-compose`. Приклад `docker-compose.yaml` знаходиться в файлі `docker-compose.example.yaml`.

```bash
docker-compose up -d
```

## Запуск в DockerSwarpm PROD

1. Формуємо оновлення в гілку master реліз

2. Формуємо новий контейнер dataslab/document_generator

3. На сервері оновлюємо репозиторій контейнерів docker pull dataslab/document_generator

4. На сервері видаляємо document-generator

5. Запускаємо формування нового стаку ./deploy
