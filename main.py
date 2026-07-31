import discord
from discord import Intents
import logging
import json
import os
import time 
from datetime import datetime, timezone
from discord.ext import commands
import config


# =========================
# CONFIG
# =========================

FILE_INFRAZIONI = os.path.join(
    os.path.dirname(__file__),
    "infrazioni.json"
)


WELCOME_CHANNEL_ID= 1532767496019644638
TICKET_CHANNEL_ID = 1532176836694638632
LOG_CHANNEL_ID = 1532176909532921976

RUOLI_WARN = [
    "FOUNDER",
    "Admin",
    "Admin chief",
    "Mod DS"
]


RUOLI_STAFF = [
    "FOUNDER",
    "Admin",
    "Admin chief",
    "Trial Mod",
    "Mod DS"
]


RUOLI_BAN = [
    "FOUNDER",
    "Admin chief",
    "Mod DS"
]

RAID_THRESHOLD = 10      # utenti
RAID_SECONDS = 15        # secondi

join_times = []
raid_attivo = False



# =========================
# BOT
# =========================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True


client = commands.Bot(
    command_prefix=".",
    intents=intents
)


logging.basicConfig(
    level=logging.INFO
)


# =========================
# FUNZIONE LOG
# =========================

async def manda_log(titolo, descrizione, colore):

    canale_log = client.get_channel(LOG_CHANNEL_ID)

    if canale_log is None:
        return


    embed = discord.Embed(
        title=titolo,
        description=descrizione,
        color=colore
    )


    await canale_log.send(
        embed=embed
    )

# =========================
# JSON
# =========================

def carica_infrazioni():

    if os.path.exists(FILE_INFRAZIONI):

        try:
            with open(FILE_INFRAZIONI, "r") as f:
                return json.load(f)

        except json.JSONDecodeError:
            return {}

    return {}



def salva_infrazioni(dati):

    with open(FILE_INFRAZIONI, "w") as f:
        json.dump(
            dati,
            f,
            indent=4
        )


# =========================
# ONLINE
# =========================

@client.event
async def on_ready():

    logging.info(
        f"Online come {client.user}"
    )

    logging.info(
        "Bot is online and ready to receive messages!"
    )



# =========================
# TICKET
# =========================

@client.command()
async def ticket(ctx, *, motivo=None):

    canale_staff = client.get_channel(
        TICKET_CHANNEL_ID
    )


    if canale_staff is None:

        await ctx.send(
            "❌ Canale staff non trovato."
        )

        return



    if motivo is None:

        await ctx.send(
            "❌ Usa: `.ticket motivo`"
        )

        return



    embed = discord.Embed(
        title="🎫 Nuova segnalazione",
        color=discord.Color.orange()
    )


    embed.add_field(
        name="👤 Segnalato da",
        value=ctx.author.mention,
        inline=False
    )


    embed.add_field(
        name="📝 Motivo",
        value=motivo,
        inline=False
    )


    await canale_staff.send(
        embed=embed
    )


    await manda_log(
        "🎫 Nuovo Ticket",
        f"{ctx.author.mention} ha aperto un ticket.\n\nMotivo:\n{motivo}",
        discord.Color.orange()
    )


    await ctx.send(
        "✅ Ticket inviato allo staff."
    )



# =========================
# STAFF
# =========================

@client.command()
async def staff(ctx):

    tag = []


    for nome in RUOLI_STAFF:

        ruolo = discord.utils.find(
            lambda r: r.name.lower() == nome.lower(),
            ctx.guild.roles
        )


        if ruolo:
            tag.append(
                ruolo.mention
            )


    if tag:

        await ctx.send(
            f"🚨 {' '.join(tag)}\nServe assistenza!"
        )


        await manda_log(
            "📢 Chiamata Staff",
            f"{ctx.author.mention} ha chiamato lo staff.",
            discord.Color.blue()
        )


    else:

        await ctx.send(
            "❌ Ruoli staff non trovati."
        )



# =========================
# BAN
# =========================

@client.command()
async def ban(ctx, membro: discord.Member = None, *, motivo="Nessun motivo"):

    autorizzato = any(
        ruolo.name in RUOLI_BAN
        for ruolo in ctx.author.roles
    )


    if not autorizzato:

        await ctx.send(
            "❌ Non puoi usare il comando ban."
        )

        return


    if membro is None:

        await ctx.send(
            "❌ Usa: `.ban @utente motivo`"
        )

        return



    try:

        await membro.ban(
            reason=motivo
        )


        await ctx.send(
            f"🔨 {membro.mention} è stato bannato.\n"
            f"Motivo: {motivo}"
        )


        await manda_log(
            "🔨 Ban effettuato",
            f"Utente: {membro.mention}\n"
            f"Staff: {ctx.author.mention}\n"
            f"Motivo: {motivo}",
            discord.Color.red()
        )


    except discord.Forbidden:

        await ctx.send(
            "❌ Non posso bannare questo utente."
        )


    except discord.HTTPException:

        await ctx.send(
            "❌ Errore durante il ban."
        )

# =========================
# UNBAN
# =========================

@client.command()
async def unban(ctx, user_id=None):

    autorizzato = any(
        ruolo.name in RUOLI_BAN
        for ruolo in ctx.author.roles
    )


    if not autorizzato:

        await ctx.send(
            "❌ Non puoi usare questo comando."
        )

        return


    if user_id is None:

        await ctx.send(
            "❌ Usa: `.unban ID_UTENTE`"
        )

        return


    try:

        user_id = int(user_id)

        utente = await client.fetch_user(
            user_id
        )


        await ctx.guild.unban(
            utente
        )


        await ctx.send(
            f"✅ {utente} è stato sbannato."
        )


        await manda_log(
            "🔓 Unban effettuato",
            f"Utente: {utente}\n"
            f"Staff: {ctx.author.mention}",
            discord.Color.green()
        )


    except ValueError:

        await ctx.send(
            "❌ L'ID inserito non è valido."
        )


    except discord.NotFound:

        await ctx.send(
            "❌ Utente non trovato."
        )


    except discord.Forbidden:

        await ctx.send(
            "❌ Non ho i permessi per sbannare."
        )


    except discord.HTTPException:

        await ctx.send(
            "❌ Errore durante l'unban."
        )



# =========================
# WARN
# =========================

@client.command()
async def warn(ctx, utente: discord.Member = None, *, motivo="Nessun motivo"):

    autorizzato = any(
        ruolo.name in RUOLI_WARN
        for ruolo in ctx.author.roles
    )


    if not autorizzato:

        await ctx.send(
            "❌ Non puoi usare questo comando."
        )

        return


    if utente is None:

        await ctx.send(
            "❌ Usa: `.warn @utente motivo`"
        )

        return



    dati = carica_infrazioni()

    uid = str(utente.id)


    if uid not in dati:

        dati[uid] = {
            "warn": [],
            "strike": []
        }


    dati[uid]["warn"].append(
        motivo
    )


    salva_infrazioni(
        dati
    )


    try:

        await utente.send(
            f"⚠️ Hai ricevuto un **warning** nel server CarlCraft\n\n"
            f"Staff: {ctx.author.mention}\n"
            f"Motivo: {motivo}\n"
            f"Totale warning: {len(dati[uid]['warn'])}"
        )


    except (discord.Forbidden, discord.HTTPException):

        pass



    await ctx.send(
        f"⚠️ {utente.mention} ha ricevuto un warning.\n"
        f"Motivo: {motivo}\n"
        f"Totale warning: {len(dati[uid]['warn'])}"
    )


    await manda_log(
        "⚠️ Warning",
        f"Utente: {utente.mention}\n"
        f"Staff: {ctx.author.mention}\n"
        f"Motivo: {motivo}",
        discord.Color.gold()
    )

# =========================
# UNWARN
# =========================

@client.command()
async def unwarn(ctx, utente: discord.Member = None, *, motivo=None):

    autorizzato = any(
        ruolo.name in RUOLI_WARN
        for ruolo in ctx.author.roles
    )


    if not autorizzato:

        await ctx.send(
            "❌ Non puoi usare questo comando."
        )

        return


    if utente is None or motivo is None:

        await ctx.send(
            "❌ Usa: `.unwarn @utente motivo`"
        )

        return


    dati = carica_infrazioni()

    uid = str(utente.id)


    if uid not in dati or len(dati[uid]["warn"]) == 0:

        await ctx.send(
            "❌ Questo utente non ha warning."
        )

        return


    if motivo not in dati[uid]["warn"]:

        await ctx.send(
            "❌ Non esiste un warning con questo motivo."
        )

        return


    dati[uid]["warn"].remove(motivo)


    salva_infrazioni(dati)


    await ctx.send(
        f"✅ Rimosso un warning a {utente.mention}\n"
        f"Motivo rimosso: {motivo}\n"
        f"Warning rimasti: {len(dati[uid]['warn'])}"
    )


    await manda_log(
        "✅ Warning rimosso",
        f"Utente: {utente.mention}\n"
        f"Staff: {ctx.author.mention}\n"
        f"Motivo rimosso: {motivo}",
        discord.Color.green()
    )



# =========================
# STRIKE
# =========================

@client.command()
async def strike(ctx, utente: discord.Member = None, *, motivo="Nessun motivo"):

    autorizzato = any(
        ruolo.name in RUOLI_WARN
        for ruolo in ctx.author.roles
    )


    if not autorizzato:

        await ctx.send(
            "❌ Non puoi usare questo comando."
        )

        return


    if utente is None:

        await ctx.send(
            "❌ Usa: `.strike @utente motivo`"
        )

        return



    dati = carica_infrazioni()

    uid = str(utente.id)


    if uid not in dati:

        dati[uid] = {
            "warn": [],
            "strike": []
        }


    dati[uid]["strike"].append(
        motivo
    )


    salva_infrazioni(
        dati
    )



    try:

        await utente.send(
            f"🚨 Hai ricevuto uno **strike** nel server CarlCraft.\n\n"
            f"Staff: {ctx.author.mention}\n"
            f"Motivo: {motivo}\n"
            f"Totale strike: {len(dati[uid]['strike'])}"
        )


    except (discord.Forbidden, discord.HTTPException):

        pass



    if len(dati[uid]["strike"]) == 3:

        await manda_log(
            "🚨 3 Strike Raggiunti",
            f"{utente.mention} ha raggiunto **3 strike**.",
            discord.Color.dark_red()
        )



    await ctx.send(
        f"🚨 {utente.mention} ha ricevuto uno strike.\n"
        f"Motivo: {motivo}\n"
        f"Totale strike: {len(dati[uid]['strike'])}"
    )


    await manda_log(
        "🚨 Strike",
        f"Utente: {utente.mention}\n"
        f"Staff: {ctx.author.mention}\n"
        f"Motivo: {motivo}",
        discord.Color.red()
    )



# =========================
# UNSTRIKE
# =========================

@client.command()
async def unstrike(ctx, utente: discord.Member = None, *, motivo=None):

    autorizzato = any(
        ruolo.name in RUOLI_WARN
        for ruolo in ctx.author.roles
    )

    if not autorizzato:
        await ctx.send(
            "❌ Non puoi usare questo comando."
        )
        return


    if utente is None or motivo is None:

        await ctx.send(
            "❌ Usa: `.unstrike @utente motivo`"
        )
        return


    dati = carica_infrazioni()

    uid = str(utente.id)


    if uid not in dati or len(dati[uid]["strike"]) == 0:

        await ctx.send(
            "❌ Questo utente non ha strike."
        )
        return


    if motivo not in dati[uid]["strike"]:

        await ctx.send(
            "❌ Non esiste uno strike con questo motivo."
        )
        return


    dati[uid]["strike"].remove(motivo)

    salva_infrazioni(dati)


    await ctx.send(
        f"✅ Rimosso lo strike di {utente.mention}\n"
        f"Motivo rimosso: {motivo}"
    )


    await manda_log(
        "✅ Strike rimosso",
        f"Utente: {utente.mention}\n"
        f"Staff: {ctx.author.mention}\n"
        f"Motivo rimosso: {motivo}",
        discord.Color.green()
    )



# =========================
# VIEW INFRACTIONS
# =========================

@client.command()
async def viewinfractions(ctx, utente: discord.Member = None):

    autorizzato = any(
        ruolo.name in RUOLI_WARN
        for ruolo in ctx.author.roles
    )


    if not autorizzato:

        await ctx.send(
            "❌ Non puoi usare questo comando."
        )

        return



    if utente is None:

        await ctx.send(
            "❌ Usa: `.viewinfractions @utente`"
        )

        return



    dati = carica_infrazioni()

    uid = str(utente.id)


    if uid not in dati:

        await ctx.send(
            f"✅ {utente.mention} non ha nessuna infrazione."
        )

        return



    warn = dati[uid]["warn"]

    strike = dati[uid]["strike"]



    embed = discord.Embed(
        title=f"📋 Infrazioni di {utente}",
        color=discord.Color.orange()
    )



    if warn:

        embed.add_field(
            name=f"⚠️ Warning ({len(warn)})",
            value="\n".join(
                f"• {motivo}"
                for motivo in warn
            ),
            inline=False
        )

    else:

        embed.add_field(
            name="⚠️ Warning",
            value="Nessun warning",
            inline=False
        )



    if strike:

        embed.add_field(
            name=f"🚨 Strike ({len(strike)})",
            value="\n".join(
                f"• {motivo}"
                for motivo in strike
            ),
            inline=False
        )

    else:

        embed.add_field(
            name="🚨 Strike",
            value="Nessuno strike",
            inline=False
        )



    embed.set_thumbnail(
        url=utente.display_avatar.url
    )


    await ctx.send(
        embed=embed
    )



# =========================
# HELLO
# =========================

@client.command()
async def hello(ctx):

    await ctx.send(
        "Ciao, ben arrivato!"
    )




# =========================
# DM
# =========================

@client.event
async def on_message(message):

    if message.author == client.user:
        return


    # DM DEL BOT
    if isinstance(message.channel, discord.DMChannel):

        testo = message.content.lower()


        if testo == "ciao":

            await message.channel.send(
                "Ciao!"
            )


        elif testo == "aiuto":

            await message.channel.send(
                "Per ricevere assistenza contatta lo staff del server."
            )


        else:

            await message.channel.send(
                "Non ho una risposta per questo."
            )

@client.event
async def on_message(message):

    if message.author == client.user:
        return

    if isinstance(message.channel, discord.DMChannel):
        testo = message.content.lower()

        if testo == "ciao":
            await message.channel.send("Ciao!")

        elif testo == "aiuto":
            await message.channel.send(
                "Per ricevere assistenza contatta lo staff del server."
            )

        else:
            await message.channel.send(
                "Non ho una risposta per questo."
            )


    # RISPOSTA AL TAG DEL RUOLO ADMIN CHIEF
    if message.role_mentions:
        for ruolo in message.role_mentions:
            if ruolo.name.lower() == "admin chief":

                await message.channel.send(
                    f"👋 Ciao {message.author.mention}, sono qui! "
                    "Come posso aiutarti?"
                )

                break

    # IMPORTANTE PER I COMANDI
    await client.process_commands(message)



@client.event
async def on_member_join(member):

    canale = client.get_channel(WELCOME_CHANNEL_ID)

    if canale is None:
        return

    embed = discord.Embed(
        title="🎉 Benvenuto!",
        description=(
            f"Ciao {member.mention}, benvenuto su **CarlCraft**!\n\n"
            "Leggi il regolamento e divertiti nella nostra SMP."
        ),
        color=discord.Color.green()
    )

    embed.set_thumbnail(url=member.display_avatar.url)

    embed.add_field(
        name="👥 Membri",
        value=str(member.guild.member_count),
        inline=True
    )

    await canale.send(embed=embed)

    global raid_attivo

    now = time.time()

    join_times.append(now)

    while join_times and now - join_times[0] > RAID_SECONDS:
        join_times.pop(0)

    if len(join_times) >= RAID_THRESHOLD and not raid_attivo:

        raid_attivo = True

        canale = client.get_channel(LOG_CHANNEL_ID)

        if canale:

            embed = discord.Embed(
                title="🚨 RAID RILEVATO",
                description=(
                    f"Sono entrati **{len(join_times)} utenti** "
                    f"in meno di **{RAID_SECONDS} secondi**."
                ),
                color=discord.Color.red()
            )

            await canale.send(embed=embed)

        return


@client.event
async def on_member_remove(member):

    canale = client.get_channel(WELCOME_CHANNEL_ID)

    if canale is None:
        return

    embed = discord.Embed(
        title="👋 Arrivederci!",
        description=f"**{member}** ha lasciato il server.",
        color=discord.Color.red()
    )

    embed.set_thumbnail(url=member.display_avatar.url)

    embed.add_field(
        name="👥 Membri rimasti",
        value=str(member.guild.member_count),
        inline=True
    )

    await canale.send(embed=embed)


@client.command()
async def raidoff(ctx):

    global raid_attivo

    if not any(r.name in RUOLI_STAFF for r in ctx.author.roles):
        await ctx.send("❌ Non hai i permessi.")
        return

    raid_attivo = False
    join_times.clear()

    await ctx.send("✅ Modalità raid disattivata.")

@client.command()
async def test(ctx):
    await ctx.send("Bot funzionante!")


client.run(config.TOKEN)