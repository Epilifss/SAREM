def get_changelog_for_version(version):
    changelog = {
        "1.1.3": {
            "titulo": "Atualizacao 1.1.3",
            "novidades": [
                "Implementado filtro por período na tela de acompanhar nova BO.",
                "Implementado filtro por período nas telas de BOs acompanhadas.",
                "Busca em tempo real ao digitar nas barras de pesquisa.",
                "Relatório com coluna de produtos e motivos por item da BO.",
            ],
            "correcoes": [
                "Melhorias de exibicao de colunas na visualizacao de relatorios.",
                "Ajustes na geracao e impressao de PDF.",
            ],
            "melhorias": [
                "Identidade visual com logo do sistema em PDF e Excel.",
                "Layout de exportacao Excel com cabecalho institucional.",
            ],
        }
    }

    default_data = {
        "titulo": f"Atualizacao {version}",
        "novidades": [
                "Filtro por periodo na tela de acompanhar nova BO.",
                "Filtro por periodo nas telas de BOs acompanhadas.",
                "Busca automatica ao digitar nas barras de pesquisa.",
                "Relatorio com produtos e motivo por item da BO.",
            ],
            "correcoes": [
                "Melhorias de exibicao de colunas na visualizacao de relatorios.",
                "Ajustes na geração e impressão de PDF.",
            ],
            "melhorias": [
                "Identidade visual com logo do sistema em PDF e Excel.",
                "Layout de exportacao Excel com cabecalho institucional.",
            ],
    }

    return changelog.get(version, default_data)
