import os
import disnake
from disnake.ext import commands
from dotenv import load_dotenv


load_dotenv()
TOKEN = os.getenv("TOKEN")

# ======================================================
# CONFIGURANDO INTENTS
# ======================================================


intents = disnake.Intents.default()
intents.members = True
intents.message_content = True

# ======================================================
# CRIANDO O BOT
# ======================================================

bot = commands.InteractionBot(intents=intents)

# ======================================================
# EVENTOS
# ======================================================
@bot.event
async def on_ready():
    """Evento chamado quando o bot estiver online e pronto para uso."""
    print(f"Bot está online! Logado como: {bot.user}")

@bot.event
async def on_member_join(member: disnake.Member):
    """
    Mensagem de boas-vindas quando um usuário entra no servidor.
    Ajuste 'channel_name' para o canal de boas-vindas que exista no seu servidor.
    """
    channel_name = "geral"  # Exemplo: "boas-vindas", "geral", etc.
    channel = disnake.utils.get(member.guild.text_channels, name=channel_name)
    if channel:
        await channel.send(f"Bem-vindo(a), {member.mention}! Fique à vontade no servidor. :)")

# ======================================================
# FUNÇÃO AUXILIAR PARA OBTER/CRIAR O CARGO "MUTED"
# ======================================================
async def get_or_create_muted_role(guild: disnake.Guild):
    """
    Retorna o cargo "Muted". Se não existir, cria e remove permissões de enviar mensagens.
    """
    role_name = "Muted"
    muted_role = disnake.utils.get(guild.roles, name=role_name)

    # Se não existir, criamos
    if not muted_role:
        try:
            muted_role = await guild.create_role(
                name=role_name,
                permissions=disnake.Permissions(send_messages=False, speak=False),
                reason="Criando cargo Muted para mutar membros."
            )
            # Remove a permissão de enviar mensagem de cada canal de texto
            for channel in guild.text_channels:
                await channel.set_permissions(muted_role, send_messages=False)
            # Remove permissão de falar de cada canal de voz
            for channel in guild.voice_channels:
                await channel.set_permissions(muted_role, speak=False)

        except Exception as e:
            print(f"Erro ao criar cargo 'Muted': {e}")
            return None

    return muted_role

# ======================================================
# SLASH COMMANDS
# ======================================================

# -------------------------- BAN --------------------------
@bot.slash_command(name="ban", description="Bane um membro do servidor.")
@commands.has_permissions(ban_members=True)
async def ban_member(
    inter: disnake.ApplicationCommandInteraction,
    member: disnake.Member,
    reason: str = None
):
    """
    Bane um membro do servidor.
    Uso: /ban @usuario [motivo]
    Permissão necessária: ban_members
    """
    # Verifica se o usuário está tentando se banir ou banir o bot
    if member == inter.author:
        await inter.response.send_message("Você não pode banir a si mesmo!", ephemeral=True)
        return
    if member == bot.user:
        await inter.response.send_message("Você não pode banir o próprio bot!", ephemeral=True)
        return

    try:
        await member.ban(reason=reason)
        await inter.response.send_message(
            f"{member.mention} foi banido(a). Motivo: {reason if reason else 'Não especificado'}"
        )
    except Exception as e:
        await inter.response.send_message(f"Não foi possível banir o usuário. Erro: {e}", ephemeral=True)

# -------------------------- KICK --------------------------
@bot.slash_command(name="kick", description="Expulsa um membro do servidor.")
@commands.has_permissions(kick_members=True)
async def kick_member(
    inter: disnake.ApplicationCommandInteraction,
    member: disnake.Member,
    reason: str = None
):
    """
    Kicka (expulsa) um membro do servidor.
    Uso: /kick @usuario [motivo]
    Permissão necessária: kick_members
    """
    if member == inter.author:
        await inter.response.send_message("Você não pode expulsar a si mesmo!", ephemeral=True)
        return
    if member == bot.user:
        await inter.response.send_message("Você não pode expulsar o próprio bot!", ephemeral=True)
        return

    try:
        await member.kick(reason=reason)
        await inter.response.send_message(
            f"{member.mention} foi expulso(a). Motivo: {reason if reason else 'Não especificado'}"
        )
    except Exception as e:
        await inter.response.send_message(f"Não foi possível expulsar o usuário. Erro: {e}", ephemeral=True)

# -------------------------- MUTE --------------------------
@bot.slash_command(name="mute", description="Muta um membro (impede de falar/teclar).")
@commands.has_permissions(manage_roles=True)
async def mute_member(
    inter: disnake.ApplicationCommandInteraction,
    member: disnake.Member,
    reason: str = None
):
    """
    Muta um membro, atribuindo o cargo "Muted".
    Uso: /mute @usuario [motivo]
    Permissão necessária: manage_roles
    """
    # Impede que alguém mute a si mesmo ou o bot
    if member == inter.author:
        await inter.response.send_message("Você não pode mutar a si mesmo!", ephemeral=True)
        return
    if member == bot.user:
        await inter.response.send_message("Você não pode mutar o bot!", ephemeral=True)
        return

    muted_role = await get_or_create_muted_role(inter.guild)
    if not muted_role:
        await inter.response.send_message("Não foi possível criar ou encontrar o cargo 'Muted'.", ephemeral=True)
        return

    if muted_role in member.roles:
        await inter.response.send_message(f"{member.mention} já está mutado(a).", ephemeral=True)
        return

    try:
        await member.add_roles(muted_role, reason=reason)
        await inter.response.send_message(
            f"{member.mention} foi mutado(a). Motivo: {reason if reason else 'Não especificado'}"
        )
    except Exception as e:
        await inter.response.send_message(f"Erro ao mutar usuário: {e}", ephemeral=True)

# -------------------------- UNMUTE --------------------------
@bot.slash_command(name="unmute", description="Desmuta um membro.")
@commands.has_permissions(manage_roles=True)
async def unmute_member(
    inter: disnake.ApplicationCommandInteraction,
    member: disnake.Member
):
    """
    Desmuta um membro, removendo o cargo "Muted".
    Uso: /unmute @usuario
    Permissão necessária: manage_roles
    """
    muted_role = disnake.utils.get(inter.guild.roles, name="Muted")
    if not muted_role:
        await inter.response.send_message("O cargo 'Muted' não existe neste servidor.", ephemeral=True)
        return

    if muted_role not in member.roles:
        await inter.response.send_message(f"{member.mention} não está mutado(a).", ephemeral=True)
        return

    try:
        await member.remove_roles(muted_role)
        await inter.response.send_message(f"{member.mention} foi desmutado(a).")
    except Exception as e:
        await inter.response.send_message(f"Erro ao desmutar usuário: {e}", ephemeral=True)

# -------------------------- ADDROLE --------------------------
@bot.slash_command(name="addrole", description="Adiciona um cargo a um membro.")
@commands.has_permissions(manage_roles=True)
async def add_role_to_member(
    inter: disnake.ApplicationCommandInteraction,
    member: disnake.Member,
    role: disnake.Role
):
    """
    Adiciona um cargo a um membro.
    Uso: /addrole @usuario @cargo
    Permissão necessária: manage_roles
    """
    if role in member.roles:
        await inter.response.send_message(
            f"{member.mention} já possui o cargo {role.name}.",
            ephemeral=True
        )
        return

    try:
        await member.add_roles(role)
        await inter.response.send_message(
            f"Cargo {role.name} adicionado a {member.mention} com sucesso!"
        )
    except Exception as e:
        await inter.response.send_message(f"Erro ao adicionar cargo: {e}", ephemeral=True)

# -------------------------- REMOVEROLE --------------------------
@bot.slash_command(name="removerole", description="Remove um cargo de um membro.")
@commands.has_permissions(manage_roles=True)
async def remove_role_from_member(
    inter: disnake.ApplicationCommandInteraction,
    member: disnake.Member,
    role: disnake.Role
):
    """
    Remove um cargo de um membro.
    Uso: /removerole @usuario @cargo
    Permissão necessária: manage_roles
    """
    if role not in member.roles:
        await inter.response.send_message(
            f"{member.mention} não possui o cargo {role.name}.",
            ephemeral=True
        )
        return

    try:
        await member.remove_roles(role)
        await inter.response.send_message(
            f"Cargo {role.name} removido de {member.mention} com sucesso!"
        )
    except Exception as e:
        await inter.response.send_message(f"Erro ao remover cargo: {e}", ephemeral=True)


# ======================================================
# EXECUTA O BOT
# ======================================================
if __name__ == "__main__":
    bot.run(TOKEN)
