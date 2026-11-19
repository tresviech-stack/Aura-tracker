# main.py - Aura Tracker for XT Hub -> Discord #stats-tracker
from flask import Flask, request, jsonify
import requests, re, os
from datetime import datetime, timezone
import zoneinfo

app = Flask(__name__)

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK", "PASTE_YOUR_STATS_TRACKER_WEBHOOK_HERE")

PH_TZ = zoneinfo.ZoneInfo("Asia/Manila")

RARITY_COLORS = {
    "basic": 0xFFFFFF, "epic": 0x9B00FF, "unique": 0x00FF00,
    "legendary": 0xFFD700, "mythic": 0xFF1493, "exalted": 0xDC143C,
    "glorious": 0x8A2BE2, "transcendent": 0xE0FFFF,
    "dimensional": 0x00008B, "challenged": 0x1A1A1A, "challenged+": 0xB30000,
}

AURA_TO_RARITY = {}
for a in ["nothing","common","uncommon","good","natural","rare","divinus","crystallized","dizzy","rage","topaz","ruby","forbidden","emerald","gilded","ink","jackpot","sapphire","wind","aquamarine"]:
    AURA_TO_RARITY[a] = "Basic"
for a in ["diaboli","umbra","penumbra","precious","hydrogen","atomic","glock","magnetic","ash","glacier","player","flora","cola","sidereum","bleeding","hellfire","flutter","targeted","watcher","flushed","hazard","doodle","rekindle","quartz","honey","lost soul","atomic: ribonucleic"]:
    AURA_TO_RARITY[a] = "Epic"
for a in ["undead","corrosive","kawaii","rage : heated","l e a k","powered","crowned","marsh","copper","watt","aquatic","lunar","solar","starlight","star rider","pleiades","flushed : lobotomy","hazard : rays","nautilus","permafrost","pulsar","constella","flow","stormal"]:
    AURA_TO_RARITY[a] = "Unique"
for a in ["fault","exotic","diaboli void","comet","divinus : angel","jade","spectre","jazz","aether","bounded","lantern","celestial","vortex","terror","hope","raven","warlock","undead : devil","kyawthuite","veylune"]:
    AURA_TO_RARITY[a] = "Legendary"
for a in ["arcane","starlight : kunzite","gothic","magnetic : reverse polarity","undefined","rage : brawler","symbiosis","astral","cosmos","obsidian","archmage","respawn","gravitational","unbound","buggify","flowed","virtual","vega","orion","parasite","apatite","savior","shift lock","evanescent","alice","bejeweled","poseidon","aquatic : flame","metabytes","wraith","zeus","lunar : full moon","solar : solstice","galaxy","moonchild","anima","twilight","astronaut","origin","hades","celestial divine","anubis","refraction","faith","hyper-volt","velocity","nautilus : lost","divinus : guardian","outlaw","spectre requiem","nightshade","soultorn","harnessed","nihility","helios","stargazer","jade // purity","amethyst"]:
    AURA_TO_RARITY[a] = "Mythic"
for a in ["starscourge","sharkyn","guardian","empty","melodic","sailor","graffiti","imaginary","hurricane","sirius","arcane : legacy","icarus","lullaby","chromatic","plasma","oculus","aviator","ruby brimstone","apotheosis","centurion","blizzard","arcane : dark","entropy","flora : florest","ethereal","fatal error","juxtaposition","overseer","exotic : apex","matrix","runic","cor lunae","twilight : iridescent memory","sentinel","antivirus","dominion","starborn","melodic : serenade","sailor : flying dutchman","carriage","aquaria","virtual // full control","virtual//ultimate","hellbound","harnessed : elements","runic:wilt","virtual : worldwide","nucleus","quartz rose"]:
    AURA_TO_RARITY[a] = "Exalted"
for a in ["chromatic : genesis","starscourge : radiant","spectraflow","lily","overture","symphony","withering grace","felled","bloodlust","gargantua","ruins","perpetual","aegis","sovereign","withered ruins","dreamscape","ascendant","matrix reality","prologue","pythios","eisveil","poseidon : atlantis","sharkyn : hammerhead"]:
    AURA_TO_RARITY[a] = "Glorious"
for a in ["nyctophobia","pixelation","luminosity","breakthrough","equinox","tree house","awakened abyssal hunter","matrix : steampunk"]:
    AURA_TO_RARITY[a] = "Transcendent"
AURA_TO_RARITY["master-hand"] = "Dimensional"
AURA_TO_RARITY["master hand"] = "Dimensional"
for a in ["meta","glitch","borealis","projection","point : zero","leviathan","memory","neferkhaf","dream catcher","true kyawthuite","true twilight","true jade"]:
    AURA_TO_RARITY[a] = "Challenged"
for a in ["astraios","hellborn","monarch","dreammetric","oppression","illusionary","tomorrow.","oblivion","crimson moon"]:
    AURA_TO_RARITY[a] = "Challenged+"
AURA_TO_RARITY["eclipse"] = "Legendary"
AURA_TO_RARITY["cell asteroides"] = "Exalted"
AURA_TO_RARITY["hyper-chroma"] = "Exalted"
AURA_TO_RARITY["a.t.l.a.s."] = "Glorious"

AURA_TO_CHANCE = {
    "arcane": "1,000,000",
    "chromatic : genesis": "1,000,000,000",
    "celestial": "350,000",
    "sovereign": "750,000,000",
    "matrix": "50,000,000",
    "glitch": "1,228,000",
    "master-hand": "10,000,000,000",
    "master hand": "10,000,000,000",
    "chromatic": "20,000,000",
    "starscourge": "10,000,000",
    "poseidon": "4,000,000",
}

def clean_name(raw):
    name = str(raw).lower().strip()
    name = re.sub(r'[★✿✦⌊⌉»«\[\]]', '', name)
    name = re.sub(r'\s+', ' ', name)
    return name.strip()

def get_actual_rarity(raw_name, chance_raw):
    key = clean_name(raw_name)
    if key in AURA_TO_RARITY:
        return AURA_TO_RARITY[key]
    try:
        c = int(re.sub(r'[^0-9]', '', str(chance_raw)))
    except:
        return "Basic"
    if c < 1000: return "Basic"
    if c < 10000: return "Epic"
    if c < 100000: return "Unique"
    if c < 1000000: return "Legendary"
    if c < 10000000: return "Mythic"
    if c < 100000000: return "Exalted"
    if c < 1000000000: return "Glorious"
    if c < 7500000000: return "Transcendent"
    return "Dimensional"

def get_true_chance(raw_name, chance_raw):
    key = clean_name(raw_name)
    if key in AURA_TO_CHANCE:
        return AURA_TO_CHANCE[key]
    try:
        c = int(re.sub(r'[^0-9]', '', str(chance_raw)))
        return f"{c:,}"
    except:
        return str(chance_raw)

@app.route("/webhook", methods=["GET", "POST"])
@app.route("/webhook/", methods=["GET", "POST"])
def handle_xt_hub():
    # XT Hub Test button does a GET check - just say OK so it doesn't 404
    if request.method == "GET":
        return jsonify({"ok": True, "status": "Aura Tracker is online!"}), 200

    data = request.get_json(silent=True) or {}
    # XT Hub sometimes sends Discord-style embeds
    if not data and request.form:
        data = dict(request.form)
    aura = data.get("aura") or data.get("name") or ""
    chance = data.get("chance") or data.get("rarity") or ""
    username = data.get("username") or data.get("player") or "Someone"

    # If XT Hub sent a Discord embed (test message), parse it
    if not aura and data.get("embeds"):
        try:
            emb = data["embeds"][0]
            text = (emb.get("title") or "") + " " + (emb.get("description") or "")
            m = re.search(r'(.+?)\s+1 in ([\d,]+)', text, re.I)
            if m:
                aura, chance = m.group(1), m.group(2)
            else:
                aura = emb.get("title") or "Test Aura"
        except:
            aura = "Test Aura"

    if not aura and data.get("content"):
        m = re.search(r'(.+?)\s+1 in ([\d,]+)', data["content"], re.I)
        if m:
            aura, chance = m.group(1), m.group(2)
        else:
            # Plain test message from XT Hub, just forward it
            aura = data["content"][:50] or "Test"

    if not aura:
        aura = "Test Aura"
    if not chance:
        chance = "1,000,000"

    # If this is just XT Hub's test, don't fail - send a test embed
    is_test = "test" in str(aura).lower() or "test" in str(data.get("content", "")).lower()

    rarity = get_actual_rarity(aura, chance)
    chance = get_true_chance(aura, chance)
    color = RARITY_COLORS.get(rarity.lower(), 0xFFFFFF)
    now = datetime.now(PH_TZ)
    rolled_text = now.strftime("%B %d, %Y - %I:%M %p")
    embed = {
        "title": f"✨ {aura} | {rarity}",
        "description": f"**{username}** rolled **{aura}**\nChance: **1 in {chance}**\nRarity: **{rarity}**\nRolled On: **{rolled_text}**",
        "color": color,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    if DISCORD_WEBHOOK and "discord.com" in DISCORD_WEBHOOK:
        requests.post(DISCORD_WEBHOOK, json={"embeds": [embed]})
    return jsonify({"ok": True, "aura": aura, "rarity": rarity, "rolled_on": rolled_text}), 200

@app.route("/", methods=["GET"])
def home():
    return "Aura Tracker is online!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
