# APEX — Regressão visual A/B (melhoria 7/8)

## Dependência obrigatória

Esta melhoria depende da **3ª melhoria**, que introduziu
`tests/ci/apex_capture_screenshots.gd` no PR #10. Para preservar uma alteração
principal por PR, o PR da regressão visual tem como base a branch
`infra/ci-capturas-graficas-v1`, não `main`.
Depois de validar e integrar o PR #10, o PR desta melhoria poderá ser
redirecionado à `main` sem duplicar a ferramenta de captura.

## O que o teste faz

- Faz checkout das duas revisões **no mesmo runner**.
- Confere que ambas têm o **mesmo script de captura**.
- Instala o mesmo Godot 4.7.2 e usa Xvfb/llvmpipe.
- Para cada revisão, captura **Silverstone 2012, seed 660, 24 carros, 1600x900**:
  - `silverstone_2d_broadcast.png`
  - `silverstone_2d_compact.png`
  - `silverstone_3d_compact.png`
- Confere a integridade dos PNGs, manifestos e que a captura preservou
  o estado esportivo.
- Calcula a diferença média absoluta de RGB (MAE) e a proporção de pixels
  cujo canal RGB máximo mudou mais que 24/255.
- Gera imagens de diferenças: áreas consideradas alteradas ficam vermelhas
  sobre a captura da referência.
- Reprova diferenças acima das tolerâncias iniciais documentadas.

| Captura | Limite pixels alterados | Limite MAE RGB |
| --- | ---: | ---: |
| HUD de transmissão 2D | 1,0% | 1,50 |
| HUD compacta 2D | 1,0% | 1,50 |
| HUD compacta 3D | 2,5% | 3,00 |

Esses limites são **heurísticos**, ainda não calibrados em GPUs de jogadores.
Não significam que toda alteração abaixo deles é desejável, nem que mudanças
acima sempre são bugs. Em ambos os casos, revisar visualmente o relatório.

## Como usar

O workflow `APEX - Regressao Visual A-B` é acionado em PRs relevantes ou
manualmente em **Actions → APEX - Regressao Visual A-B → Run workflow**.

A execução manual recebe duas referências: `baseline_ref` e `candidate_ref`.
Enquanto o PR #10 não estiver integrado, use como referência
`infra/ci-capturas-graficas-v1`. Depois da integração, `main` poderá ser a
referência, desde que contenha o script de captura.

Abra os detalhes da execução e baixe o artifact `apex-regressao-visual-ab`.
Ele contém imagens da referência, da versão candidata, mapas de diferenças,
manifestos, logs e `report.json`/`report.md`.

## Limites de cobertura

A ferramenta examina apenas três **quadros fixos** da HUD e do circuito,
não animações, replays, IA, desempenho, FPS ou comportamento de corrida completa.
A comparação **não é executada** se o script de captura mudar entre as
versões: primeiro é preciso estabilizar novamente o cenário de teste.

A saída e o status do GitHub são calculados com os dados medidos; nunca
simulam ou substituem um resultado por uma imagem inventada. O cenário é
controlado, mas o llvmpipe pode introduzir ruído. Revisar qualquer falha
e distinguir regressão real de variabilidade antes de corrigir o jogo.

## Preservação

Nenhum script da simulação, HUD ou save é alterado por esta melhoria.
O workflow não faz merge, release nem modificação automática de imagens-base.
