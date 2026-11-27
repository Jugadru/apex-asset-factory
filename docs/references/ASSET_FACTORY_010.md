# APEX Asset Factory — v0.1.0 Infrastructure & Procedural Build

## Escopo e contrato
Versão independente do Core 2/Hyper. Reusa Foundation (plan, inspect_glb) e Graphics Lab (inspect PNG). A PR #177 é dependência; não fundir automaticamente. Não alterar física, saves, UI, assets existentes ou instalações permanentes.

- Entrada: tools/asset_factory/request.schema.json v1, uma solicitação original por execução. Apenas car, 2012-inspired, original-low-poly, LOD0, sem fontes externas. approved: true habilita somente a geração demonstrativa, não autentica usuário nem aprova promoção. seed varia o acento de pintura, não a geometria; dimensões e pintura são parametrizadas.
- Execução: Blender confiável, Godot confiável e workspace novo fora do repositório; chamadas sem shell, timeout por processo, arquivos criados sem sobrescrever. Não é sandbox OS: executar somente código revisado em ambiente descartável. Nenhum download ou instalação de serviço.
- Saída: GLB, projeto Godot isolado, captura opcional, plan.json, request.json, registry.json, report.json, logs. Registry por execução, não catálogo global; não há reserva central de IDs.
- QA: contêiner GLB, triângulos, presença de POSITION/NORMAL/TEXCOORD_0, nomes de quatro rodas, índice de material, ausência de texturas (v0.1.0 não tem texturas), importação real, envelope com tolerância de 2%, captura PNG. Não é validador glTF completo; não comprova UV sem sobreposição, normais corretas em todas as faces, pivôs geometricamente exatos, escala de cada componente ou LODs. Sem promoção automática.
- Coordenadas: Blender +Y frente / +Z cima; Godot -Z frente / +Y cima; medidas em metros. Escala do envelope pode deformar rodas: demonstração, não especificação técnica FIA.
- Agente autorizado: execução local por CLI; publicação/PR via credenciais do conector, fora do CLI; autorização externa ao JSON. Sem runner pessoal ou workflow dispatch sem autorização.
- Falha: conservar workspace e logs; corrigir e usar novo workspace. Rollback: descartar branch/PR ou reverter somente commit da fábrica. Nenhum asset do jogo foi trocado.

## Executar

    python3 -m unittest discover -s tools/tests -p 'test_asset_factory.py' -v
    python3 tools/asset_factory/build.py tools/asset_factory/demo.json --blender /caminho/blender --godot /caminho/godot --workspace /tmp/apex-asset-demo-novo --capture

Blender 5.3.x e Godot 4.7.2.x; Xvfb/Xauth e OpenGL Compatibility para captura em Linux. --capture é opcional, sem ele visual NOT_RUN. CI de contratos reaproveita FAST; build nativo requer executáveis e autorização de execução. Nenhuma publicação.

## Evidências de execução local
- Blender 5.3.0 Release Candidate f78a5e153839; Godot 4.7.2.stable.official.ed1daf0bf.
- 6 testes Python PASS (inclui 10 entradas inválidas); GLB 202120 bytes, 2952 triângulos de orçamento 8000, 5 materiais, 28 meshes Godot, envelope 1.80000007 x 1.10000002 x 4.80000067 m (X/Y/Z).
- Primeira execução: export/import PASS, captura FAIL por DISPLAY inválido; segunda execução: captura PNG 960x540 PASS com Xvfb/Mesa llvmpipe e áudio Dummy. Aviso VSync, sem GPU física ou FPS medido.
- GLB SHA256: 335858afdd0268182e5c82e7a452dc86eb9930b83c657155c1557cb3c562dbdb. PNG SHA256: 85ed891f42bc349293847d74156d1e660f0901239e57b4061f3062df5c089dc5.
- Duas exportações mesma seed: JSON glTF idêntico, 88 accessors, 14 UV com diferenças float máximas 5.96e-8, demais accessors exatos; SHA de arquivo diferente. Repetibilidade geométrica observada, byte determinístico não garantido.
- Não executado: homologação no jogo completo/FAST do candidato, revisão humana final, importação de terceiros, texturas/baking, LOD, animação, aprovação, promoção.
- Cópias dos seis novos arquivos confrontadas pelos hashes Git com commit edafa3396521e8d6e25172c3d43480f06d761861. Para ensaio local foram usados os trechos efetivos de plan, inspect_glb e inspect lidos do SHA da Foundation, não checkout integral. CI deve testar com dependências completas.

## Roadmap incremental (proposto, não implementado)
| Versão | Uma capacidade principal | Gate |
|---|---|---|
| 0.1.1 | Hardening do validator GLB e equivalência geométrica | validar buffers, índices, finitude, pivôs, UV, falhas e seed |
| 0.1.2 | Registry persistente e versionado | IDs reservados, histórico append-only, hashes, licenças revisadas, locks |
| 0.1.3 | Build receipts e CI/Lab bridge | proprietário e SHA exato, artefatos, timeouts, sem shell arbitrário |
| 0.2.0 | Vehicle components | chassi modular, eixos, rodas, wings, cockpit e sockets |
| 0.2.1 | Vehicle variants | eras, GT, endurance, formação e liveries originais |
| 0.2.2 | LOD e budgets | LOD0/1/2, pivôs e métricas de distância/performance |
| 0.3.0 | Material & Texture Factory | PBR, UV, baking, mapas, texturas e licenças |
| 0.3.1 | Superfícies dinâmicas | molhado, sujeira, desgaste visual sem alterar simulação |
| 0.4.0 | Circuit Generator base | spline autorizada, asfalto, largura, elevação, continuidade |
| 0.4.1 | Circuit kit | pit lane, zebras, barreiras, câmeras, alinhamento visual somente leitura |
| 0.4.2 | Environment Factory | boxes, garagens, oficinas, fábrica, paddock, instâncias |
| 0.5.0 | Character Factory | personagens e capacetes originais, uniformes, rig |
| 0.6.0 | Animation Factory veículos | rodas, direção, DRS, suspensão e danos |
| 0.6.1 | Animation Factory pessoal | pit crew, mecânicos, engenheiros, eventos e clips |
| 0.7.0 | Audio Factory experimental | motores sintéticos, pneus, pit, ambiente; sem clonagem de voz |
| 0.8.0 | Godot Integration Pipeline | adaptadores de produção, import presets, cenas, capturas multiângulo e regressão |
| 0.9.0 | Autonomous Build Pipeline | aprovação vinculada a hash, PR somente após licença/QA, recuperação |
| 1.0.0 | Estabilidade | auditoria completa, regressões, documentação, rollback, operação autorizada |

Não avançar enquanto o gate anterior não estiver comprovado. A futura extração para apex-asset-factory dependerá de contrato estável, custo real de manutenção e autorização para criar repositório.
