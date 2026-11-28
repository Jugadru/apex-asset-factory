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

## Complemento de migração — contratos e continuidade
Manifesto expandido para 32 blobs de origem verificados por comparação de Git SHA, incluindo contratos Foundation e guias de QA; snapshots somente leitura. Handoff e inventário SHA256 dos runtimes registrados. CI da revisão ampliada precisa de PASS antes de aceitar; FAST do jogo continua pendente. Nenhuma licença ou autorização de promoção inferida da migração.

## v0.1.1 — candidate evidence (PR #3)
- AF-B008: PARTIAL/PASS for synthetic supported static untextured indexed GLB subset; native acceptance and broader glTF profiles NOT_RUN. Evidence: https://github.com/Jugadru/apex-asset-factory/actions/runs/45928355798 (17 unit tests, source SHA f96ca0313d80888b2f996283904e123a896246b0).
- AF-B007: numeric comparator implemented and synthetic tests PASS; actual repeated native exports and multi-seed test NOT_RUN in v0.1.1; binary identity not established. AF-B009: finite unit normals, zero-area triangles, named wheel nodes and scene references tested; pivot/UV overlap/scale/visual QA pending. AF-B021: strict JSON constants rejected; request schema and resource security incomplete.
- AF-B003: upstream Foundation PR #177 closed without merge; investigate successor before integration. AF-B005: local DNS still blocks direct checkout; hosted checkout PASS. Native v0.1.1 Blender/Godot rerun pending. No merge/promotion; v0.1.1 stacked on open migration PR #1. Do not close IDs merely on synthetic CI.

## Hyper candidate — v0.1.5
Machine-readable [ledger](docs/blockers.json) is current. AF-B007 PASS for numeric equivalence in supported profile only (byte identity FAIL); AF-B008 PASS for static untextured indexed profile. AF-B012 local registry, backup/restore and rollback tests PASS, prebuild reservation/multi-host pending. AF-B013/014 signed local package gate tested, actual owner key/rights/review and remote authorization pending. AF-B015 bounded process runner tested, OS sandbox/RAM/network pending. AF-B003 original #177 closed unmerged, #192 documentary only. AF-B004 hosted CI PASS, game FAST pending. AF-B005 DNS blocks full local clone; ten exact native files and four builds PASS. AF-B006 RC checksums verified. AF-B011 software capture PASS only. AF-B016 remote dispatch blocked. AF-B019 offline handoff and native harness only. Other graphical factories remain planned. [Native evidence](https://github.com/Jugadru/apex-asset-factory/blob/feature/v0.1.2-0.1.5-infrastructure/evidence/v0.1.5-native/summary.json), [CI](https://github.com/Jugadru/apex-asset-factory/actions/runs/46018529079).

### Reservation follow-up
AF-B012 PASS in single-host registry scope: prebuild claims, conflict, explicit release after failure, consumption, immutability, local concurrency, rollback and backup/restore verified by 28-test CI https://github.com/Jugadru/apex-asset-factory/actions/runs/46019032367. Distributed queue and shared multi-host execution remain AF-B019; no permanent service. Five original IDs are PASS within their recorded scope. Ten native source blobs remain identical in this candidate.

## v0.2.0 candidate
AF-B009/B017 partial: modular layouts and export-wheel QA implemented, 34 unit tests PASS, native balanced pair PASS and earlier wide variant PASS; final wide batch timeout, remaining native low-drag and legacy rerun pending. No new blocker closed, no production release. See https://github.com/Jugadru/apex-asset-factory/blob/feature/v0.2.0-modular-vehicle/evidence/v0.2.0-native/summary.json.

### v0.2.0 native follow-up
Separate native runs completed for wide, low-drag and legacy, all stages PASS. Historical batch timeout retained but resolved. AF-B017 PASS for modular original open-wheel scope only; AF-B009 partial; visual review, GPU physical and game integration NOT_RUN.

## v0.2.1 candidate
AF-B018 partial: three era-inspired open-wheel silhouettes, native export/import/capture PASS for each. GT/endurance and other factories remain unimplemented. AF-B009 partial: shaped meshes and wheel QA pass but detailed visual/UV/physical GPU acceptance pending. No new ID closed. Evidence: https://github.com/Jugadru/apex-asset-factory/blob/feature/v0.2.1-era-vehicles/evidence/v0.2.1-native/summary.json.

## v0.2.1.1 candidate
AF-B009 partial: actual recessed cockpit, era halo, 20 visual suspension links; 144 analytic layouts and four native exports pass with GLB cavity and wheel QA. UV, visual acceptance, detailed mechanics and Godot articulation remain pending. No new ID closed. Evidence: https://github.com/Jugadru/apex-asset-factory/blob/feature/v0.2.1.1-cockpit-suspension/evidence/v0.2.1.1-native/summary.json.

## v0.2.1.2 candidate
AF-B009 and AF-B018 partial: two original closed-wheel categories, continuous shell and sampled wheel clearance. 45 tests PASS, 32 analytic dimensional combinations, two exact-source native builds PASS. Previous visual quality rejected by owner; current models remain stylized, no production approval. No new blocker closed. Evidence: https://github.com/Jugadru/apex-asset-factory/blob/feature/v0.2.1.2-closed-wheel/evidence/v0.2.1.2-native/summary.json.

## v0.2.2 candidate
AF-B010 partial: procedural LOD0/1/2, 51 tests PASS, nine native variants with unchanged dimensions/component counts and three Godot switch fixtures. GT and endurance outer timeouts recovered separately, openwheel full orchestrator PASS. Texture/UV/PBR, schema 2/3 native tests, packaging, visual and physical GPU/game acceptance pending. Six IDs scoped PASS unchanged. https://github.com/Jugadru/apex-asset-factory/blob/feature/v0.2.2-automatic-lod/evidence/v0.2.2-native/summary.json

## v0.2.3 candidate
AF-B009/B010 partial: curved closed-wheel surface profiles, sampled clearance, 96 analytic cases and four native variants. GT three LODs and separate 11-step switch PASS; endurance LOD0 PASS. Endurance LOD1/2, visual acceptance, physical GPU, textures and game integration pending. No new blocker closed. https://github.com/Jugadru/apex-asset-factory/blob/feature/v0.2.3-advanced-body/evidence/v0.2.3-native/summary.json

## Review follow-up
Native schema 2/3 and curved endurance lower LODs completed. Four numeric repeat comparisons PASS (one binary identical). 15 new builds, 55 switch steps and 12 exact targeted unit tests PASS. Current remote CI remains FAIL with inaccessible logs and no recorded steps; no complete current suite or CI success claim. See https://github.com/Jugadru/apex-asset-factory/blob/feature/v0.2.3-advanced-body/evidence/v0.2.3-review/summary.json. No new blocker closed; no promotion.

## Native results
96 analytic dimension/tire/LOD combinations; four exact targeted tests PASS. Six final native LOD variants and extra GT capture build PASS, 28 detailed wheel parts each, max local exported vertex error <1e-6 m. GT 15080/8168/4904 triangles, endurance 15116/8236/4940. GT full orchestration PASS; endurance timeout during switch, recovered separately with receipt/identity/budget gates and 11-step Godot switch PASS. Three actual software captures (GT, endurance and isolated GT wheel). 47 exact source/test/request blobs matched; full local checkout remains blocked by DNS. Formal repeatability, openwheel wheel detail, artist approval, physical GPU and game integration pending. Private evidence ZIP 237 files, CRC checked. https://github.com/Jugadru/apex-asset-factory/blob/feature/v0.2.4-wheel-brake-detail/evidence/v0.2.4-native/summary.json

## Native evidence
66 CI tests PASS (46076802259); 432 analytic combinations, 54 exact local Git blobs, nine native Blender/Godot variants and three complete orchestrators with 33 switch checks PASS. 1990: 11692/6764/4204 triangles; 2012: 11804/6844/4252; 2020: 12200/7176/4520. 28 wheel parts each, maximum exported local vertex error 1.45e-8 m (rounded upward). Six separate software captures PASS. Initial preview failed because the suffix selector included suspension nodes; fixed exact whitelist and retained history. Private ZIP 241 files, CRC checked, runtime caches removed. Formal repeatability, physical GPU, artistic approval and game integration remain NOT_RUN. No new blocker closed, no promotion. https://github.com/Jugadru/apex-asset-factory/blob/feature/v0.2.4.1-openwheel-detail/evidence/v0.2.4.1-native/summary.json

## Native PBR evidence
Six final variants, six Blender and six Godot native imports PASS; three software captures PASS; 11 LOD switch checks and 16 matching texture hashes across 2012 LODs. 16 exact source/dependency/test blobs, four targeted local tests PASS. GT LOD2 512px native test PASS (512px is a larger sampling of the same 256-cell procedural pattern, not added detail). GT initial grainy paint capture retained; final modulation reduced and retested. Original geometry buffer/accessors/meshes/nodes preserved exactly in all six outputs. UV degeneracy audit: 84 per 2012 LOD, 164/128 GT LOD0/2, 172 endurance LOD0. No UV repair, normal maps, baking, arbitrary textured GLB validator, texture residency budget, artistic acceptance or game integration. Private ZIP 133 files, CRC checked. No new blocker closed. https://github.com/Jugadru/apex-asset-factory/blob/feature/v0.3.0-material-texture-factory/evidence/v0.3.0-native/summary.json

## Native evidence
Six final variants (five at 256px, one at 512px), 716 collapsed UV triangles repaired to zero. 58,000 triangles, 174,000 indexed corners' positions and normals and all originally valid UV coordinates preserved exactly. Six Blender and six Godot import UV count checks PASS, three software captures and 11 switch steps PASS, 16 equal map hashes across 2012 LODs. 18 exact local Git blobs, four new and four existing targeted tests PASS. Two batch timeouts recovered separately; no false pass. Private ZIP 143 entries, CRC checked. UV overlap and production atlas remain untested; no new blocker closed, no promotion. https://github.com/Jugadru/apex-asset-factory/blob/feature/v0.3.0.1-uv-repair/evidence/v0.3.0.1-native/summary.json

## Native evidence
Six final native variants, 162 embedded maps, 58,000 triangles, 174,000 Blender corner tangents and 62,404 Godot vertex tangents checked. Three software captures; 11 switch steps and 24 equal map hashes across the 2012 LODs. 20 exact source blobs and 12 targeted local tests PASS (4 new, 8 regressions). Carbon relief reduced after initial capture; six final variants rerun. Timeout cases recovered separately, initial GT capture retained. Private ZIP 105 files CRC clean. No high-poly baking, atlas, AO, physical GPU, artistic acceptance or game integration. No new blocker closed. https://github.com/Jugadru/apex-asset-factory/blob/feature/v0.3.0.2-normal-detail/evidence/v0.3.0.2-native/summary.json
