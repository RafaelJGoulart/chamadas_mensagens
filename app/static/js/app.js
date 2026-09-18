(function () {
    "use strict";

    var menuContexto = null;
    var opcoesEstado = [
        { valor: "ausente", rotulo: "Marcar como ausente", classe: "botao-perigo" },
        { valor: "frequente", rotulo: "Marcar como frequente", classe: "botao-primario" },
        { valor: "reposicao", rotulo: "Marcar como reposição", classe: "botao-repo" },
    ];

    /* ---- Confirmar exclusão ---- */
    function abrirConfirmacao(titulo, mensagem, aoConfirmar) {
        var fundo = document.createElement("div");
        fundo.className = "modal-fundo";

        var modal = document.createElement("div");
        modal.className = "modal";
        modal.setAttribute("role", "dialog");
        modal.setAttribute("aria-modal", "true");
        modal.setAttribute("aria-labelledby", "modal-titulo");

        var hTitulo = document.createElement("h2");
        hTitulo.id = "modal-titulo";
        hTitulo.textContent = titulo || "Confirmar exclusão";

        var texto = document.createElement("p");
        texto.textContent = mensagem;

        var acoes = document.createElement("div");
        acoes.className = "modal-acoes";

        var botaoCancelar = document.createElement("button");
        botaoCancelar.type = "button";
        botaoCancelar.className = "botao botao-secundario";
        botaoCancelar.textContent = "Cancelar";

        var botaoConfirmar = document.createElement("button");
        botaoConfirmar.type = "button";
        botaoConfirmar.className = "botao botao-perigo";
        botaoConfirmar.textContent = "Confirmar";

        acoes.append(botaoCancelar, botaoConfirmar);
        modal.append(titulo, texto, acoes);
        fundo.append(modal);
        document.body.append(fundo);
        fundo.classList.add("aberto");

        function fechar() {
            fundo.remove();
            document.removeEventListener("keydown", aoTeclado);
        }

        function aoTeclado(ev) {
            if (ev.key === "Escape") fechar();
        }

        botaoCancelar.addEventListener("click", fechar);
        fundo.addEventListener("click", function (ev) {
            if (ev.target === fundo) fechar();
        });
        document.addEventListener("keydown", aoTeclado);
        botaoConfirmar.focus();
        botaoConfirmar.addEventListener("click", function () {
            fechar();
            aoConfirmar();
        });
    }

    document.addEventListener("submit", function (ev) {
        var form = ev.target;
        var mensagem = form.dataset.confirma;
        if (!mensagem) return;
        ev.preventDefault();
        abrirConfirmacao(
            form.dataset.confirmaTitulo,
            mensagem,
            function () { form.submit(); }
        );
    });

    /* ---- Menu de presença (usado pela matriz da turma) ---- */
    function fecharMenu() {
        if (menuContexto) {
            menuContexto.remove();
            menuContexto = null;
        }
    }

    function abrirMenuEstado(anchor, estadoAtual, aoEscolher) {
        fecharMenu();

        var menu = document.createElement("div");
        menu.className = "menu-contexto";
        menu.setAttribute("role", "menu");

        opcoesEstado.forEach(function (opcao) {
            var botao = document.createElement("button");
            botao.type = "button";
            botao.className = "menu-item menu-item-" + opcao.classe.replace("botao-", "");
            botao.textContent = opcao.rotulo;
            botao.setAttribute("role", "menuitem");

            if (opcao.valor === estadoAtual) {
                botao.classList.add("menu-item-ativo");
            }

            botao.addEventListener("click", function () {
                fecharMenu();
                aoEscolher(opcao.valor);
            });

            menu.append(botao);
        });

        document.body.append(menu);
        menuContexto = menu;

        var rect = anchor.getBoundingClientRect();
        var topo = rect.bottom + 4;
        var esq = Math.min(rect.left, window.innerWidth - 230);

        menu.style.position = "fixed";
        menu.style.top = topo + "px";
        menu.style.left = esq + "px";
        menu.style.zIndex = 100;
    }

    window.SistemaChamadas = window.SistemaChamadas || {};
    window.SistemaChamadas.abrirMenuEstado = abrirMenuEstado;
    window.SistemaChamadas.fecharMenu = fecharMenu;

    document.addEventListener("click", function (ev) {
        if (menuContexto && !menuContexto.contains(ev.target)) {
            fecharMenu();
        }
    });

    /* ---- Filtro instantâneo de tabelas (componente _pesquisa.html) ---- */
    function normalizarBusca(texto) {
        return (texto || "")
            .toLowerCase()
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "");
    }

    document.addEventListener("input", function (ev) {
        var campo = ev.target && ev.target.closest
            ? ev.target.closest("[data-filtro-tabela]")
            : null;
        if (!campo) return;
        var corpo = document.getElementById(campo.getAttribute("data-filtro-tabela"));
        if (!corpo) return;
        var termo = normalizarBusca(campo.value.trim());
        var visiveis = 0;
        corpo.querySelectorAll("tr:not(.linha-sem-resultado)").forEach(function (tr) {
            var base = tr.getAttribute("data-filtro") || tr.textContent;
            var mostra = !termo || normalizarBusca(base).indexOf(termo) !== -1;
            tr.hidden = !mostra;
            if (mostra) visiveis += 1;
        });
        var semResultado = corpo.querySelector(".linha-sem-resultado");
        if (semResultado) semResultado.hidden = visiveis !== 0;
        var idContagem = campo.getAttribute("data-filtro-contagem");
        if (idContagem) {
            var contagem = document.getElementById(idContagem);
            if (contagem) {
                contagem.textContent = termo
                    ? visiveis + " resultado(s) na tela"
                    : "";
            }
        }
    });

    /* ---- Fechar avisos (flash) ---- */
    function esconderFlash(flah) {
        flah.style.transition = "opacity 0.25s, transform 0.25s";
        flah.style.opacity = "0";
        flah.style.transform = "translateY(-4px)";
    }

    document.addEventListener("click", function (ev) {
        var botaoFechar = ev.target.closest(".flash-fechar");
        if (!botaoFechar) return;
        var flah = botaoFechar.closest(".flash");
        if (flah) esconderFlash(flah);
    });

    document.addEventListener("keydown", function (ev) {
        if (ev.key === "Escape") fecharMenu();
    });

})();