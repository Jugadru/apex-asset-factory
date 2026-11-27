# Decisão do responsável — 26/11/2026
Separar a produção gráfica em `Jugadru/apex-asset-factory`, versionamento próprio. Preferência técnica: privado inicialmente, README inicial e main. O repositório não está acessível (404 e ausente da listagem); conector não possui ação de criação de repositórios. Não criar serviço permanente, não solicitar token em chat.

## Base preservada
- [PR #184](https://github.com/Jugadru/APEX-Simulation/pull/184), draft, head `f878b09aa5d66ef7d8302b2d94aa2a8d7db9c59b`, base Foundation `884e6c60b4b3ba8ca06a52850ee8ed097b9f7e18`. NÃO MERGE como implementação de produção; manter histórico até migração verificada.
- [PR #177](https://github.com/Jugadru/APEX-Simulation/pull/177), draft e não integrada na consulta. FAST da revisão Foundation run 45923094403 success; não equivale ao FAST #184.
- Evidência histórica local registrada na documentação da #184: Blender 5.3.0 RC, Godot 4.7.2, 6 testes Python PASS, GLB 2952 triângulos, 28 meshes, 5 materiais, captura 960x540 via Xvfb/llvmpipe. Não reexecutados nesta atualização documental.

## Registro de bloqueios e limitações (IDs permanentes)
| ID | Prioridade | Estado | Limitação / critério para resolver |
|---|---|---|---|
| AF-B001 | P0 | PASS | Repo público criado; leitura/escrita verificadas via commits e PR #1. |
| AF-B002 | P0 | PASS | Migração em PR #1: 25/25 blobs idênticos, 10 testes CI e fixture nativa PASS. Merge da PR e integração no jogo são decisões separadas. #184 preservada sem merge. |
| AF-B003 | P0 | BLOCKED | Foundation #177 não integrada; fixar versão/SHA dos contratos compartilhados, registrar compatibilidade e evitar duas implementações autoritativas. |
| AF-B004 | P0 | NOT_RUN | CI próprio e FAST candidato: testes do novo repo e integração no jogo em PR direcionada a main, com PASS no SHA exato; não impor FULL. |
| AF-B005 | P1 | BLOCKED | Clone completo anterior indisponível; reexecutar com checkout completo e dependências reais, não cópias parciais dos helpers. |
| AF-B006 | P1 | NOT_RUN | Blender disponível é RC, não release final; verificar runtime exato, origem, checksum, compatibilidade e matriz de versões. |
| AF-B007 | P1 | INCONCLUSIVE | Binário não reproduzível: JSON igual, 14 de 88 accessors UV diferiram até 5,96e-8; definir tolerância geométrica e testar seeds/revisões, sem exigir SHA igual indevidamente. |
| AF-B008 | P1 | NOT_RUN | GLB validator parcial: validar chunks, buffers/accessors, índices, finitude, dependências e extensões, malhas vazias/degeneradas, integridade e limites. |
| AF-B009 | P1 | NOT_RUN | Presença de normais/UVs não certifica qualidade: verificar orientação, degeneração, UV overlap, escala por peça, pivôs, sockets, rodas/hubs e eixos. |
| AF-B010 | P1 | NOT_RUN | Texturas, baking, mapas PBR reais e LODs ainda ausentes; testar orçamentos e compatibilidade. |
| AF-B011 | P1 | NOT_RUN | GPU física, FPS, VRAM, inspeção visual humana e regressões visuais no jogo completo não avaliados; captura llvmpipe prova somente renderização fixture. |
| AF-B012 | P1 | NOT_RUN | Registro por execução, sem catálogo global, reserva de IDs, locks, histórico append-only ou controle de concorrência; implementar persistência e rollback. |
| AF-B013 | P0 | BLOCKED | Aprovação/promoção/publicação: não publicar assets sem direitos, revisão humana, hashes e aprovação vinculada à versão; impedir sobrescrita de assets aprovados. |
| AF-B014 | P0 | NOT_RUN | JSON approved não autentica agente; implementar autorização externa e permissões mínimas, manter aprovação separada da execução. |
| AF-B015 | P1 | NOT_RUN | Workspace e timeout não equivalem a sandbox OS; estabelecer isolamento, limites CPU/RAM/disco, processos filhos e recuperação. |
| AF-B016 | P1 | BLOCKED | Conector não oferece dispatch geral de workflow; usar gatilhos de PR/CI e bridge autorizado, sem runner pessoal não autorizado. |
| AF-B017 | P2 | NOT_RUN | Somente monoposto original simplificado 2012-inspired, LOD0; seed altera acento da pintura, não geometria; escala anisotrópica pode deformar rodas. Validar peças intercambiáveis e variantes antes de chamar gerador completo. |
| AF-B018 | P2 | NOT_RUN | GT/endurance/formação, circuitos, ambientes, personagens, animações, danos, áudio, ingestão externa: não implementados. Roadmap incremental; sem clonagem de voz ou cópia proprietária. |
| AF-B019 | P1 | NOT_RUN | Pipeline ainda não possui aprovação/PR automatizada, filas de jobs, retries controlados, recuperação e bridge end-to-end; testar política de autorização e recibos de execução. |
| AF-B020 | P1 | NOT_RUN | Distribuição de binários/assets grandes e política Git LFS/artefatos/releases ainda não validadas; decidir retenção, tamanho, licenças e acesso. |
| AF-B021 | P1 | NOT_RUN | Schema restrito e validador parcial; testar tipos estritos, números não finitos, limites de entrada/logs, erros de ferramenta, contrato de saída/registry, segurança de caminhos; evitar manutenção duplicada de schemas. |
| AF-B022 | P1 | NOT_RUN | Geometria de pista ainda sem contrato implementado de sincronização com trajetória esportiva somente leitura; testar independência de resultados e hashes no jogo. |
| AF-B023 | P1 | NOT_RUN | Direitos de referências/terceiros não revalidados; manter fontes externas bloqueadas até prova de licença, autoria, origem e redistribuição. |
| AF-B024 | P1 | NOT_RUN | Licença de código do novo repo e de distribuição de assets originais ainda não escolhida pelo proprietário; não presumir licença permissiva. |

## Incidente resolvido (histórico)
AF-R001 — captura inicial falhou por DISPLAY inacessível. Reexecução com Xvfb/llvmpipe e áudio Dummy PASS local. Não implica suporte GPU física ou CI novo.

## Migração: critérios de aceite
1. Criar repo privado inicializado, verificar acesso. 2. Migrar código e docs da #184 em PR própria, com dependências compartilhadas fixadas e procedência; não copiar runtime do jogo. 3. Criar AGENTS.md, BLOCKERS.md/JSON e roadmap; adicionar CI de contratos e testes nativos opt-in. 4. Reexecutar a demo com logs e SHA exato. 5. Só depois marcar #184 superseded e integrar no jogo apenas manifesto/adaptador versionado, sem modelos não aprovados. 6. Fechar IDs somente com evidência e link para teste/PR; manter histórico de FAIL, BLOCKED e NOT_RUN.

A nova fábrica é dona de fontes gráficas, geradores, staging, QA e registro; Foundation é dona dos contratos compartilhados; APEX-Simulation é consumidor de assets aprovados e autoridade esportiva. Não duplicar Engineering Lab ou Graphics Lab. Nenhum merge/publicação/alteração esportiva autorizados por este registro.

## Atualização de migração
AF-B001 PASS: acesso leitura/escrita confirmado em Jugadru/apex-asset-factory, público. AF-B002: transferência candidata; confirmar hashes, CI e execução antes de encerrar. AF-B004: CI de contratos adicionado, execução ainda NOT_RUN até evidência. Demais IDs e evidências históricas preservados. Descrição original de repo inexistente é histórica. Fonte: APEX-Simulation issue #187. Distribuição permanece BLOCKED (AF-B013/024); repo público não implica licença de assets.

## Evidências da migração (PR #1)
- AF-B001 PASS e AF-B002 PASS no escopo de transferência e validação da branch; ver evidências em `evidence/v0.1.0-migration/`.
- AF-B004 CI independente PASS (10 testes, 25 blobs); FAST no jogo ainda NOT_RUN/BLOCKED por integração separada.
- AF-B005 checkout hospedado do novo repo PASS; clone local direto continua BLOCKED por DNS. Fixture local executada com nove arquivos de hashes Git exatos, incluindo três helpers completos.
- AF-B006 runtime RC f78a5e153839 verificado; release final/matriz ainda NOT_RUN.
- AF-B007 nova exportação possui SHA GLB diferente, captura PNG com SHA idêntico; determinismo binário ainda INCONCLUSIVE.
- AF-B015 execução no container descartável como root gerou aviso Godot; não configura sandbox endurecido. AF-B011 captura via llvmpipe com aviso VSync; GPU física e revisão humana permanecem NOT_RUN.
