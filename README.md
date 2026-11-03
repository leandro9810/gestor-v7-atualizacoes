# Atualizações do Gestor de Projetos V7

Repositório público de distribuição dos arquivos do programa. Os bancos SQLite, cadastros de clientes, projetos, backups, tokens e arquivos de controle permanecem no computador do usuário e não devem ser enviados para este repositório.

## Funcionamento

O inicializador local consulta `manifesto.json` na branch `main` antes de iniciar o servidor, quando o Gestor está encerrado. Novas versões são baixadas por HTTPS e verificadas por SHA-256. O atualizador faz backup dos programas e do banco e permite restaurar os programas anteriores se a verificação inicial de saúde falhar.

A primeira versão de teste é 7.0.1. A verificação inicial não substitui os testes das funcionalidades.

## Publicação pela integração do GitHub

A conexão autorizada do ChatGPT permite preparar e publicar alterações neste repositório durante uma conversa. A conexão foi validada por leitura e atualização deste README. Ela não cria melhorias nem executa publicações sem uma tarefa solicitada.

Para cada melhoria:

1. Ler a versão atual dos arquivos e preservar a compatibilidade com o banco instalado.
2. Desenvolver e testar a alteração.
3. Incrementar `version` no manifesto, no formato de três números inteiros.
4. Calcular o SHA-256 dos bytes exatos de cada arquivo distribuído.
5. Publicar os arquivos e o manifesto de forma consistente, preferencialmente em um único commit. Para pacotes com vários arquivos, usar URLs imutáveis dos arquivos em um commit de conteúdo e só depois atualizar o manifesto público.
6. Conferir a publicação. O computador recebe a versão ao encerrar e abrir novamente o Gestor pelo inicializador configurado.

O atualizador instalado aceita somente `servidor.py`, `interface.html` e `backup_diario.py`. Alterações no próprio atualizador ou inicializador exigem instalação separada. Migrações de banco ainda não são suportadas.

## Configuração local

O arquivo local `atualizacoes.json` aponta para:

`https://raw.githubusercontent.com/leandro9810/gestor-v7-atualizacoes/main/manifesto.json`

A busca depende de `enabled: true` e de conexão à internet. Sem uma nova versão publicada, o Gestor mantém a versão instalada.
