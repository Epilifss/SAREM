O SAREM é um sistema de desktop robusto projetado para o gerenciamento de Boletins de Ocorrência (BOs). Ele oferece uma interface gráfica intuitiva, construída com Tkinter, para facilitar o registro, a consulta e a administração de ocorrências em diferentes setores de uma organização.

Principais Funcionalidades:
Autenticação de Usuário: O sistema possui uma tela de login para garantir que apenas usuários autorizados tenham acesso.
Módulos de Visualização: A aplicação é dividida em módulos, como Corporativo, Varejo e Exportação, permitindo que diferentes perfis de usuários visualizem apenas as informações pertinentes ao seu setor.
Listagem e Pesquisa: Os usuários podem visualizar uma lista completa de BOs e realizar pesquisas rápidas para encontrar registros específicos.
Visualização de Detalhes: É possível abrir uma janela modal para ver todos os detalhes de um BO específico.
Edição de Registros: Usuários com as devidas permissões podem editar as informações de um Boletim de Ocorrência existente.
Interface Organizada: O layout é composto por componentes reutilizáveis, como cabeçalho, barra de pesquisa e uma tabela (Treeview) para exibição dos dados, garantindo uma experiência de usuário consistente.
Arquitetura:
O projeto segue uma arquitetura bem definida, separando as responsabilidades:

front/: Contém toda a lógica da interface do usuário, incluindo janelas, modais e componentes visuais.
back/: Gerencia a lógica de negócios, o acesso ao banco de dados e os serviços da aplicação (gerenciamento de usuários e BOs).
theme/: Centraliza a estilização dos componentes da interface, permitindo uma aparência coesa.
assets/: Armazena os ícones e imagens utilizados na aplicação.
O SAREM é uma solução completa para empresas que precisam de um sistema interno para rastrear e gerenciar incidentes e ocorrências de forma eficiente e segura.
