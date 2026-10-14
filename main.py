import random, string
from fastapi import FastAPI, Request, Form, status
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from utils import load_words

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="super_secret_key")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Загрузка словарей
WORDS_RU = load_words("words_ru.txt")
WORDS_EN = load_words("words_en.txt")

ALPHABET_RU = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
ALPHABET_EN = string.ascii_uppercase
MAX_ATTEMPTS = 7

MESSAGES = {
    "ru": {
        "tip": "Введите одну букву (русскую)",
        "attempts": "Осталось попыток",
        "won": "Победа! Слово:",
        "lost": "Проигрыш. Слово было:"
    },
    "en": {
        "tip": "Enter one letter (English)",
        "attempts": "Attempts left",
        "won": "You won! Word:",
        "lost": "You lost. Word was:"
    }
}

def new_game(lang="ru"):
    words = WORDS_RU if lang == "ru" else WORDS_EN
    word = random.choice(words)
    return {"word": word, "guessed": [], "misses": [], "status": "playing", "lang": lang}

def get_mask(word, guessed):
    return " ".join([ch if ch in guessed else "＿" for ch in word])

def check_win(word, guessed):
    return all(ch in guessed for ch in set(word))

@app.get("/")
async def index(request: Request):
    if "game" not in request.session:
        request.session["game"] = new_game()
    game = request.session["game"]
    mask = get_mask(game["word"], game["guessed"])
    attempts_left = MAX_ATTEMPTS - len(game["misses"])
    return templates.TemplateResponse("index.html", {
        "request": request,
        "game": game,
        "mask": mask,
        "attempts_left": attempts_left,
        "messages": MESSAGES[game["lang"]],
    })

@app.post("/guess")
async def guess_letter(request: Request, letter: str = Form(...)):
    game = request.session.get("game", new_game())
    if game["status"] != "playing":
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    letter = letter.strip().upper()
    alphabet = ALPHABET_RU if game["lang"] == "ru" else ALPHABET_EN
    if len(letter) != 1 or letter not in alphabet:
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    if letter in game["guessed"] or letter in game["misses"]:
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    if letter in game["word"]:
        game["guessed"].append(letter)
        if check_win(game["word"], game["guessed"]):
            game["status"] = "won"
    else:
        game["misses"].append(letter)
        if len(game["misses"]) >= MAX_ATTEMPTS:
            game["status"] = "lost"
    request.session["game"] = game
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/restart")
async def restart(request: Request):
    lang = request.session.get("game", {}).get("lang", "ru")
    request.session["game"] = new_game(lang)
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/set-lang")
async def set_lang(request: Request, lang: str = Form(...)):
    if lang not in ("ru", "en"):
        lang = "ru"
    request.session["game"] = new_game(lang=lang)
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)

if __name__ == '__main__':
    app.run('localhost:8000')