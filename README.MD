# AI Engineer Challenge: The Intelligent Scheduler

## Sobre este teste

Este teste avalia sua capacidade de **resolver um problema usando AI como ferramenta** — não apenas de escrever código. Você terá AI liberada durante a execução, e por isso o que estamos avaliando é diferente: queremos ver como você pensa antes de codar, como instrui a AI, como revisa o que ela produz, e como justifica suas decisões.

---

## Formato

| Fase | Duração   | Atividade                  | AI permitida? |
| ------| -----------| ----------------------------| ---------------|
| 1    | 10 min    | Leitura e dúvidas          | —             |
| 2    | 60 min    | Especificação (documento)  | Não           |
| 3    | 50 min    | Execução (código)          | Sim           |
| 4    | 20–30 min | Recap síncrono (outro dia) | —             |

### Como funciona o cronômetro

As fases 1, 2 e 3 são feitas **presencialmente**, em sequência, com um avaliador presente. Ele acompanha o tempo de cada fase. Você ainda anota início e fim no `CHANGES.md` — fica como registro para o recap. A Fase 4 é agendada depois, remota.

### Fase 1 — Leitura e dúvidas (10 min)

Leia o enunciado inteiro. Tire dúvidas com o avaliador **antes** de começar a Fase 2 — ele está ali pra responder. As perguntas que você faz também são avaliadas: elas mostram como você aborda um problema novo.

Sempre pergunte em caso de dúvidas.

### Fase 2 — Especificação (60 min, sem AI, sem código)

Nesta fase você escreve o documento que vai orientar a Fase 3. Pense nele como o documento que você daria a um colega para que ele implementasse a solução sozinho — ou que você daria a um agente de AI pra gerar a implementação.

**Não use AI nesta fase.** Use editor de texto comum.

O **estilo é livre**. Organize do jeito que fizer sentido. Avaliamos pela qualidade dos artefatos, não pelo formato.

O documento precisa cobrir cinco áreas. Em 30 min, **priorize concisão** — bullets diretos, sem prosa.

1. **Princípios de design.** Entre 3 e 5 decisões transversais que valem pro projeto inteiro. Não são features — são regras como "estado é fonte única da verdade", "toda chamada de API tem timeout explícito", "saída de LLM nunca vai direto pra outro nó sem validação". Uma linha cada.

2. **Especificação funcional.** Lista das capacidades do agente, cada uma com critérios de aceite no formato "dado X, quando Y, espero Z". Cubra as 4 situações descritas em [O que o agente precisa resolver](#o-que-o-agente-precisa-resolver). Critérios de aceite precisam ser verificáveis — "agente lida bem com erros" não é critério; "se `/availability` retornar 500, o agente responde com a mensagem M e oferece tentar de novo" é.

3. **Plano técnico.** Modelo de estado tipado + diagrama do fluxo do agente (estados possíveis e transições — ASCII, mermaid ou esboço serve) + justificativa da escolha de framework. Não precisa de prosa explicativa longa — o diagrama e a tipagem do estado falam.

4. **Estratégia de prompts.** Para cada momento em que o agente usa LLM: objetivo, contexto de entrada, formato de saída esperado, como validar a saída, fallback se falhar. **Esta é a seção que diferencia este teste de um design doc tradicional** — você está especificando como vai instruir a AI, não só o código. Não pule.

5. **Plano de execução.** Lista ordenada do que você vai implementar primeiro. Inclua o que você corta se o tempo apertar.

> **Entregável mínimo:** todas as 5 áreas presentes, com a especificação funcional cobrindo as 4 situações do enunciado e a estratégia de prompts cobrindo pelo menos os momentos críticos de uso de LLM. Sem isso, a Fase 3 fica sem direção e o recap fica difícil.

### Fase 3 — Execução (50 min, com AI)

Implemente sua solução. Use a AI da forma que preferir (Cursor, Copilot, Claude, ChatGPT — você escolhe).

**O tempo é curto de propósito.** Em 60 min você não consegue implementar tudo com qualidade alta — e isso faz parte do que avaliamos. Priorize: entregar 60% bem-feito é melhor que 100% mal-feito. Use o plano de execução da Fase 2 como guia, e documente o que ficou de fora.

**Requisitos obrigatórios desta fase:**

- **Documente desvios do plano e o que ficou de fora.** Escreva no `CHANGES.md` o que mudou em relação à Fase 2 e o que você decidiu não implementar (e por quê). Mudanças justificadas são valorizadas; cortes silenciosos levantam dúvidas.

- **Use sua spec como contexto da AI.** Você pode (não é obrigatório) usar o documento da Fase 2 como contexto direto pros prompts da Fase 3 — passando ele inteiro ou em pedaços. Se fizer isso, deixe claro no histórico. Vamos avaliar quão bem sua spec serviu de input pra AI: spec ruim gera código ruim, e isso vira sinal real de qualidade do que você escreveu na Fase 2.

### Fase 4 — Recap síncrono (20–30 min, agendado após a entrega)

Conversa com o avaliador em outro dia. Você pode (e deve) consultar seu código, sua spec e seu histórico de prompts durante o recap.

As perguntas cobrem três eixos:

- **Decisões técnicas.** Por que esse modelo de estado, por que esse fluxo, por que essa escolha de framework, etc.
- **Uso de AI.** Onde a AI errou e como você percebeu? Que prompt funcionou mal e como ajustou? Quando você discordou da sugestão dela e por quê?
- **Evolução do sistema.** Como você adicionaria X? Como escalaria pra Y? O que você implementaria se tivesse mais 60 min?

---

## O problema

Você está construindo o backend de um bot de WhatsApp para um hospital. Pacientes mandam mensagens como:

- *"Quero marcar uma ressonância pra terça que vem."*
- *"Posso agendar um exame de sangue?"*
- *"Na verdade, esquece a ressonância, marca um raio-X."*

O agente precisa conduzir a conversa, validar o paciente, checar disponibilidade, informar instruções de preparo, e confirmar o agendamento. Não é uma CLI — é um assistente.

### Stack

- **Orquestração de agente:** sua escolha. LangGraph, LangChain, LlamaIndex, framework próprio, ou direto com chamadas de LLM e máquina de estados — todos são aceitos. **Justifique a escolha na Fase 2.**
- **Interface com LLM:** Amazon Bedrock (fornecemos uma short-term API key). O scaffolding já traz um wrapper mínimo em `llm.py` usando `boto3.bedrock-runtime.converse`; você pode trocar pelo Anthropic SDK (`anthropic[bedrock]`) ou qualquer abordagem equivalente, desde que continue usando Bedrock.
- **Linguagem:** Python 3.10+.

### API mockada

Em `api/exam_scheduler.py`. **Você pode modificá-la livremente** se precisar.

| Endpoint           | Método | Propósito                                            |
| --------------------| --------| ------------------------------------------------------|
| `/patients/{id}`   | GET    | Valida o paciente. 200 se existe, 404 se não.        |
| `/service-catalog` | GET    | Lista exames disponíveis e instruções de preparo.    |
| `/availability`    | GET    | Retorna slots para um exame e uma data (YYYY-MM-DD). |
| `/appointments`    | POST   | Cria o agendamento.                                  |

Para subir a API:

```bash
uv run uvicorn api.exam_scheduler:app --reload --port 8080
```

Docs em http://127.0.0.1:8080/docs.

### Interface de chat

Há um `app.py` com Chainlit pra você testar o agente conversacionalmente:

```bash
uv run chainlit run app.py
```

Disponível em http://localhost:8000.

### Configuração

Copie `.env.example` para `.env` e preencha:

```
AWS_BEARER_TOKEN_BEDROCK=<chave-fornecida-pelo-avaliador>
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0
API_BASE_URL=http://127.0.0.1:8080
```

`AWS_BEARER_TOKEN_BEDROCK` é a [short-term API key do Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/api-keys.html) — `boto3 ≥ 1.39` lê esta variável automaticamente, então **você não precisa configurar `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`**. Se preferir trocar de modelo (Haiku para iterar mais barato, por ex.), basta editar `BEDROCK_MODEL_ID`.

---

## O que o agente precisa resolver

Em vez de listar fluxos numerados, listamos **situações** que o agente precisa atender. Como você modela isso (estado, grafo, prompts) é parte do que estamos avaliando.

### Capacidades funcionais

- Validar a identidade do paciente antes de qualquer booking. Formato: começa com `P` seguido de alfanuméricos.
- Identificar a intenção do usuário e extrair tipo de exame e data desejada da conversa.
- Solicitar informações que estiverem faltando, sem ser repetitivo.
- Informar instruções de preparo (jejum, etc.) **antes** de o usuário confirmar o slot.
- Apresentar slots disponíveis e finalizar o booking quando o usuário confirma.

### Situações que o agente precisa lidar bem (obrigatórias)

1. **Ambiguidade temporal.** Usuário diz "terça que vem" numa sexta-feira de noite. Que data o agente assume? E se for sábado de madrugada? E se disser apenas "amanhã" às 23:55? Documente sua decisão.

2. **Resiliência a falha de API.** `/availability` retorna 500. `/availability` retorna lista vazia. `/appointments` retorna conflito (slot já reservado entre o GET e o POST). O agente não pode travar nem dar resposta genérica de "erro interno" — precisa orientar o usuário.

3. **Patient ID inválido vs malformado.** Validação por regex e validação no servidor são coisas diferentes — uma falha por formato (`INVALID123` não começa com `P`), outra por inexistência (`P99999` tem formato certo mas não existe). O agente trata as duas situações de forma distinta?

4. **Informações fora de ordem.** Usuário pode mandar o patient ID antes de pedir um exame, ou pedir o exame antes de mandar o ID, ou mandar tudo junto numa frase. O agente lida com qualquer ordem sem perguntar coisas que já foram respondidas.

### Bônus (se sobrar tempo)

- **Mudança de ideia no meio do fluxo.** Usuário pediu ressonância, agente já mostrou slots, usuário diz "ah, na verdade quero raio-X". Idealmente o grafo lida com isso sem reiniciar a conversa. Se for cíclico só no nome mas linear na prática, conta como linear.

### Restrições técnicas

- A arquitetura deve suportar **fluxo agêntico** — capacidade de o agente decidir o próximo passo com base no estado, não só seguir um pipeline fixo. Cadeia linear com `if/else` espalhados não atende.
- O **estado da conversa** deve estar tipado e ser explícito (não escondido em variáveis globais ou no histórico de mensagens cru).
- **Transições de estado** devem ser declarativas — dá pra olhar o código e entender quais são os estados possíveis e como se transita entre eles, sem caçar pelo arquivo todo.
- **Chamadas a tools/APIs** devem estar separadas da lógica de raciocínio do LLM.
- **Tratamento de erro** não pode depender de exceções não capturadas.

### Tom de voz do bot

O hospital exige que as mensagens sigam este padrão:

- Sempre em português, formal mas acolhedor (trato por "você", não "o senhor/a senhora").
- Nunca dar diagnóstico nem opinião médica.
- Sempre mencionar instruções de preparo **antes** de confirmar slot, nunca depois.
- Em caso de erro de sistema, não expor detalhes técnicos ao usuário.

Como você garante isso na implementação é parte do problema.

---

## Critérios de avaliação

A avaliação considera todas as 4 fases, com pesos:

- **Fase 2 (Especificação) — 70%.** Qualidade dos princípios de design, clareza e completude da especificação funcional, solidez do plano técnico, **profundidade da estratégia de prompts**, realismo do plano de execução. Esta é a fase de maior peso porque o teste avalia primariamente sua capacidade de especificar problemas de forma que humanos e AIs consigam executar.
- **Fase 3 (Execução) — 20%.** Funcionamento (cobre as situações descritas), qualidade do código, qualidade do uso de AI (prompts iterativos, revisão crítica, não-aceitação cega de sugestões), aderência ou desvio justificado em relação à spec.
- **Fase 4 (Recap) — 10%.** Capacidade de justificar decisões, autoconsciência sobre uso de AI, profundidade ao discutir evolução do sistema.

**Importante:** O peso baixo da Fase 3 **não significa que ela pode ser ignorada**. Spec excelente com código que não roda ou que claramente não foi executado é sinal vermelho — significa que você não conseguiu validar a própria spec. Esperamos código funcional que cubra pelo menos o happy path e um caso de erro, demonstrando que sua spec é implementável.

---

## Entregáveis

Envie tudo num único repositório (fork deste ou novo):

1. Documento de especificação da Fase 2 (markdown, txt, ou PDF) — ex.: `SPEC.md` na raiz.
2. Código da solução.
3. Histórico de interações com AI da Fase 3 (arquivo, link ou pasta).
4. `CHANGES.md` com: horário de início e fim de cada fase, desvios em relação à Fase 2, e o que ficou de fora.

Envie tudo antes do recap. Não atualize nada após o envio — o recap é sobre o que você entregou, não sobre o que você queria ter entregue.

---

## Dúvidas frequentes

**Qual framework de orquestração devo usar?** O que você dominar melhor. LangGraph, LangChain, LlamaIndex, código próprio com máquina de estados — todos servem, desde que o resultado atenda as restrições técnicas. A escolha em si é avaliada (pela justificativa que você dá na spec), não a opção específica.

**Posso usar AI na Fase 2?** Não. Queremos ver como *você* especifica o problema antes de instruir a AI.

**Posso usar Google Fase 2?** Sim, pode usar pra tirar dúvidas e até aprender algum conceito ou ler documentação.

**Preciso seguir uma metodologia específica de SDD?** Não. Se você conhece Spec Kit, Kiro, BDD ou outro framework, à vontade. Se não, organize do jeito que fizer sentido. Avaliamos os artefatos, não o vocabulário.

**E se eu não terminar a Fase 3 em 60 min?** Pare. O tempo é parte da avaliação. Entregar 60% bem-feito é melhor que 100% mal-feito. Liste o que faltou no `CHANGES.md`.

**Posso mudar a API mockada?** Sim, à vontade. Documente as mudanças.

**Posso adicionar libs além das obrigatórias?** Sim, desde que justifique.

**Vocês vão olhar meus prompts?** Sim. É parte central da avaliação.

**E se a AI me der uma solução melhor que a do meu plano?** Ótimo. Adapte, justifique no `CHANGES.md`, e esteja pronto pra defender no recap.
