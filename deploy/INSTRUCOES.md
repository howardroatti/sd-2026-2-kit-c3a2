# Do repositório-base à entrega

## 1. Publicar a base no GitHub

1. Entre no GitHub e abra o [kit do professor](https://github.com/howardroatti/sd-2026-2-kit-c3a2). Clique em **Fork → Create fork**. Sugestão de nome: `c3a2-plataforma-ia-base`. Escolha o perfil que vai manter a base.
2. Na pasta local já revisada, adicione um remoto separado para evitar publicar no kit:

   ```bash
   git remote add base https://github.com/SEU_USUARIO/c3a2-plataforma-ia-base.git
   git push -u base main
   ```

   Se o repositório-base já existir com outro nome, use a URL dele. O `push` requer acesso autenticado à conta.

3. Confira o README e o histórico pelo GitHub. Para compartilhar sem depender de uma conta, a partir da pasta local gere `git bundle create ../c3a2-plataforma-ia-base.bundle main`. O colega pode usar `git clone -b main c3a2-plataforma-ia-base.bundle`; o arquivo contém o histórico e deve ficar fora do repositório.

## 2. Criar o repositório final e trabalhar em grupo

1. Em uma **organização ou conta diferente** da que mantém a base, crie um fork da base com nome `c3a2-plataforma-ia`. O GitHub admite um fork da mesma rede por proprietário; a organização do grupo permite ter base e entrega separadas.
2. Convide os integrantes em **Settings → Collaborators** (ou conceda acesso de escrita pela organização). Cada integrante deve clonar o **mesmo** repositório final:

   ```bash
   git clone https://github.com/ORGANIZACAO/c3a2-plataforma-ia.git
   cd c3a2-plataforma-ia
   git switch -c melhoria/minha-tarefa
   # Faça e teste sua alteração.
   git add CAMINHO_DO_ARQUIVO
   git commit -m "Descreva a melhoria realizada"
   git push -u origin HEAD
   ```

3. Abram pull requests para `main`, revisem entre vocês e prefiram **Create a merge commit** se desejam preservar cada commit na branch principal. Antes de começar outra tarefa, façam `git switch main` e `git pull --ff-only`.
4. Sugestões de contribuições: integrar a inferência ou o worker de trabalhos anteriores do grupo, validar falhas e traces, e realizar o deploy/documentar resultados. Cada pessoa faz commits próprios; não é preciso sobrescrever commits, copiar autores ou usar `push --force`.

## 3. Publicar em HTTPS

Requisitos: uma VM Linux com Docker Engine atualizado e Compose v2, IPv4 público e um domínio/subdomínio controlado pela equipe. Exemplo de free tier: **Oracle Cloud Always Free**, se houver capacidade na região. Confira no painel se VM e disco estão elegíveis antes de criar; disponibilidade e limites são do provedor. Pode usar um subdomínio gratuito que permita apontar o DNS para a VM.

1. No DNS, crie um registro **A** para o IPv4 público da VM. Remova eventual registro AAAA incorreto. No firewall da nuvem e da VM, libere TCP **80/443** e restrinja SSH ao IP de administração. Não libere as portas internas.
2. Na VM, clone o **repositório final**. Na raiz dele, configure:

   ```bash
   umask 077
   cp .env.example .env
   openssl rand -hex 32
   ```

   Edite `.env`: informe `DOMINIO` sem `https://` nem barra final (`ia.exemplo.com`), use o valor gerado em `JWT_SEGREDO` e configure `USUARIOS` com contas de teste e senhas fortes (mínimo de 12 caracteres, sem vírgulas). Não publique `.env` nem as senhas no GitHub.

3. Suba a aplicação e o proxy:

   ```bash
   docker compose -f docker-compose.yml -f compose.publico.yml up -d --build --wait
   docker compose -f docker-compose.yml -f compose.publico.yml logs --tail=100 caddy
   ```

   Caddy emite e renova o certificado TLS quando o DNS e a rede estão corretos. Para acessar o Jaeger da VM, use `ssh -L 16686:127.0.0.1:16686 USUARIO@IP_DA_VM`.

   **Variante com Traefik já existente** (usada em `ia.arthurssrichard.com`): se a VM já tem um Traefik ocupando 80/443, com a rede Docker externa `proxy` e um certificado padrão (por exemplo, Cloudflare Origin com o DNS em modo proxy), troque o override do Caddy por `compose.traefik.yml`. Só o gateway entra na rede `proxy`, e `/metrics` fica de fora do roteamento:

   ```bash
   docker compose -f docker-compose.yml -f compose.traefik.yml up -d --build --wait
   ```

4. Valide de outra máquina:

   ```bash
   curl -fsS https://ia.exemplo.com/saude
   read -rs -p 'Senha do usuário de teste: ' SENHA; echo
   BASE=https://ia.exemplo.com USUARIO=avaliador SENHA="$SENHA" python3 scripts/fumaca.py
   unset SENHA
   ```

   Configure `avaliador` na VM ou substitua pelo nome escolhido. Além do teste público, faça um clone limpo em outra máquina e rode `docker compose up --build --wait` e `python3 scripts/fumaca.py` com os valores locais.

5. Preencha no `README.md` do repositório final os três nomes, a URL **real** e um contato autorizado. Envie ao professor o acesso de demonstração por um canal privado. Na atividade **C3.A2** do AVA, poste apenas a URL do repositório final. Se o AVA exigir arquivo, envie um documento contendo somente esse link.
