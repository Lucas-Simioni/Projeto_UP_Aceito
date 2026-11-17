/* Aceito! — comportamento das telas.
   Tudo aqui é melhoria progressiva: sem JavaScript as páginas continuam funcionando
   (formulários enviam normalmente e o servidor valida todas as regras). */
(function () {
  "use strict";

  const $ = (seletor, raiz = document) => raiz.querySelector(seletor);
  const $$ = (seletor, raiz = document) => Array.from(raiz.querySelectorAll(seletor));

  /* ---------------------------------------------------------------- menu do celular */
  const botaoMenu = $("[data-menu]");
  const menu = $("#menu-principal");
  if (botaoMenu && menu) {
    botaoMenu.addEventListener("click", () => {
      const aberto = menu.classList.toggle("aberto");
      botaoMenu.setAttribute("aria-expanded", String(aberto));
      botaoMenu.setAttribute("aria-label", aberto ? "Fechar menu" : "Abrir menu");
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && menu.classList.contains("aberto")) {
        menu.classList.remove("aberto");
        botaoMenu.setAttribute("aria-expanded", "false");
        botaoMenu.focus();
      }
    });
  }

  /* ---------------------------------------------------------------- mensagens */
  function fecharMensagem(el) {
    el.classList.add("sumindo");
    setTimeout(() => el.remove(), 300);
  }
  $$("[data-fechar]").forEach((botao) =>
    botao.addEventListener("click", () => fecharMensagem(botao.closest(".mensagem")))
  );
  // Avisos e sucessos somem sozinhos (seção 15); erros ficam até o usuário fechar.
  $$(".mensagem[data-some]").forEach((el) => setTimeout(() => fecharMensagem(el), 7000));

  /* ---------------------------------------------------------------- confirmação C01 (RF15) */
  const janelaConfirmar = $("#janela-confirmar");
  let formularioPendente = null;
  $$("form[data-confirmar]").forEach((form) => {
    form.addEventListener("submit", (evento) => {
      if (form.dataset.confirmado === "1") return;
      evento.preventDefault();
      if (!janelaConfirmar || typeof janelaConfirmar.showModal !== "function") {
        if (window.confirm(form.dataset.confirmar)) { form.dataset.confirmado = "1"; form.submit(); }
        return;
      }
      formularioPendente = form;
      $("[data-texto]", janelaConfirmar).textContent = form.dataset.confirmar;
      const ok = $("[data-confirmar-ok]", janelaConfirmar);
      const acao = form.dataset.confirmarBotao || "Excluir";
      ok.textContent = acao;
      ok.className = "botao " + (acao === "Excluir" ? "botao-perigo" : "botao-primario");
      $("#janela-confirmar-titulo").textContent = acao === "Excluir" ? "Confirmar exclusão" : "Confirmar";
      janelaConfirmar.showModal();
      $("[data-cancelar]", janelaConfirmar).focus();
    });
  });
  if (janelaConfirmar) {
    $("[data-confirmar-ok]", janelaConfirmar).addEventListener("click", () => {
      janelaConfirmar.close();
      if (formularioPendente) { formularioPendente.dataset.confirmado = "1"; formularioPendente.submit(); }
    });
  }

  /* ---------------------------------------------------------------- janela de pagamento (UC09) */
  const janelaPagar = $("#janela-pagar");
  if (janelaPagar && typeof janelaPagar.showModal === "function") {
    const formPagar = $("form", janelaPagar);
    const campoData = $("#janela-data-pagamento", janelaPagar);
    const hoje = campoData.value;
    $$("[data-pagar]").forEach((link) => {
      link.addEventListener("click", (evento) => {
        evento.preventDefault();
        formPagar.action = link.dataset.pagar;
        $("[data-descricao]", janelaPagar).textContent = link.dataset.descricao;
        $("[data-valor]", janelaPagar).textContent = link.dataset.valor;
        $("[data-vencimento]", janelaPagar).textContent = link.dataset.vencimento;
        campoData.value = hoje;
        campoData.min = link.dataset.minimo;
        janelaPagar.showModal();
        campoData.focus();
      });
    });
    formPagar.addEventListener("submit", () => {
      const botao = $("button[type=submit]", formPagar);
      botao.disabled = true; // evita duplo clique (o servidor também confere "já está paga?")
    });
  }

  $$("dialog.janela").forEach((janela) => {
    $$("[data-cancelar]", janela).forEach((b) => b.addEventListener("click", () => janela.close()));
    janela.addEventListener("click", (e) => { if (e.target === janela) janela.close(); });
  });

  /* ---------------------------------------------------------------- filtros que se aplicam sozinhos */
  $$("form[data-autoenvio] select").forEach((select) =>
    select.addEventListener("change", () => select.form.submit())
  );

  /* ---------------------------------------------------------------- valores em reais: 1.234,56 */
  // A pessoa digita como preferir ("4000", "4.000", "4000,5", "4.000,00"); ao sair do campo o valor
  // é mostrado como 4.000,00. A leitura segue a mesma regra do servidor (interpretar_moeda).
  function formatarMoeda(texto) {
    let limpo = texto.replace(/R\$/g, "").replace(/\s/g, "");
    if (!limpo) return "";
    if (limpo.includes(",")) limpo = limpo.replace(/\./g, "").replace(",", ".");
    else if (/^\d{1,3}(\.\d{3})+$/.test(limpo)) limpo = limpo.replace(/\./g, "");
    const partes = /^(\d+)(?:\.(\d{0,2}))?$/.exec(limpo);
    if (!partes) return texto; // inválido: deixa como está e o servidor explica o erro
    const inteiro = partes[1].replace(/^0+(?=\d)/, "").replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return inteiro + "," + (partes[2] || "").padEnd(2, "0");
  }
  $$("input[data-moeda]").forEach((campo) => {
    if (campo.readOnly) return;
    campo.addEventListener("input", () => {
      const filtrado = campo.value.replace(/[^\d.,]/g, "");
      if (filtrado !== campo.value) campo.value = filtrado;
    });
    campo.addEventListener("blur", () => { campo.value = formatarMoeda(campo.value); });
  });

  /* ---------------------------------------------------------------- máscara de telefone */
  $$("input[data-telefone]").forEach((campo) => {
    campo.addEventListener("input", () => {
      const d = campo.value.replace(/\D/g, "").slice(0, 11);
      let v = d;
      if (d.length > 2) v = `(${d.slice(0, 2)}) ${d.slice(2)}`;
      if (d.length > 6) {
        const meio = d.length === 11 ? 7 : 6;
        v = `(${d.slice(0, 2)}) ${d.slice(2, meio)}-${d.slice(meio)}`;
      }
      campo.value = v;
    });
  });

  /* ---------------------------------------------------------------- regras da senha (T02) */
  const campoSenha = $("input[data-senha]");
  if (campoSenha) {
    const regras = {
      tamanho: (s) => s.length >= 8,
      letra: (s) => /[A-Za-zÀ-ÿ]/.test(s),
      numero: (s) => /\d/.test(s),
    };
    const atualizar = () => $$("[data-regra]").forEach((li) =>
      li.classList.toggle("atendida", regras[li.dataset.regra](campoSenha.value))
    );
    campoSenha.addEventListener("input", atualizar);
    atualizar();
  }

  /* ---------------------------------------------------------------- formulário de despesa (T08) */
  const formDespesa = $("form[data-form-despesa]");
  if (formDespesa) {
    const categoria = $("#categoria_id", formDespesa);
    const fornecedor = $("#fornecedor_id", formDespesa);
    const categoriaPorFornecedor = JSON.parse(formDespesa.dataset.fornecedores || "{}");

    // RN13: só mostra fornecedores da categoria escolhida; escolher o fornecedor ajusta a categoria.
    const filtrarFornecedores = () => {
      const cat = categoria.value;
      Array.from(fornecedor.options).forEach((opcao) => {
        if (!opcao.value) return;
        const pertence = !cat || String(categoriaPorFornecedor[opcao.value]) === cat;
        opcao.hidden = !pertence;
        opcao.disabled = !pertence;
      });
      if (fornecedor.selectedOptions[0] && fornecedor.selectedOptions[0].disabled) fornecedor.value = "";
    };
    categoria.addEventListener("change", filtrarFornecedores);
    fornecedor.addEventListener("change", () => {
      const cat = categoriaPorFornecedor[fornecedor.value];
      if (cat && String(cat) !== categoria.value) { categoria.value = String(cat); filtrarFornecedores(); }
    });
    filtrarFornecedores();

    // Pré-visualização das parcelas calculada pelo servidor (mesma regra RN07/RN08 de quando salva).
    const valor = $("#valor_total", formDespesa);
    const parcelas = $("#num_parcelas", formDespesa);
    const vencimento = $("#primeiro_vencimento", formDespesa);
    const destino = $("[data-previa-conteudo]", formDespesa);
    let espera = null;
    let ultimaConsulta = "";

    const escapar = (t) => String(t).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

    async function atualizarPrevia() {
      if (!valor.value || !parcelas.value || !vencimento.value) return;
      const consulta = new URLSearchParams({ valor: valor.value, parcelas: parcelas.value, vencimento: vencimento.value }).toString();
      if (consulta === ultimaConsulta) return;
      ultimaConsulta = consulta;
      try {
        const resposta = await fetch(`${formDespesa.dataset.previaUrl}?${consulta}`, { headers: { Accept: "application/json" } });
        const dados = await resposta.json();
        if (!dados.ok) {
          destino.innerHTML = `<p class="previa-vazia">${escapar(dados.erro || "Confira os valores informados.")}</p>`;
          return;
        }
        const apos = dados.parcelas.filter((p) => p.apos_casamento).length;
        destino.innerHTML =
          `<ul class="previa-lista">${dados.parcelas.map((p) =>
            `<li class="${p.apos_casamento ? "apos" : ""}"><span>${p.numero}ª · ${escapar(p.vencimento)}${p.apos_casamento ? " · após o casamento" : ""}</span><strong>${escapar(p.valor)}</strong></li>`
          ).join("")}</ul>` +
          (apos ? `<p class="previa-aviso">${apos} parcela(s) vencem depois da data do casamento.</p>` : "") +
          `<div class="previa-total"><span>${dados.parcelas.length}x</span><span>Total ${escapar(dados.total)}</span></div>`;
      } catch (erro) {
        ultimaConsulta = "";
      }
    }
    [valor, parcelas, vencimento].forEach((campo) =>
      campo.addEventListener("input", () => { clearTimeout(espera); espera = setTimeout(atualizarPrevia, 350); })
    );
    if (!valor.readOnly) atualizarPrevia();
  }
})();
