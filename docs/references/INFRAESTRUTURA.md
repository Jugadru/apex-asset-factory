# APEX Foundation — arquitetura-alvo e contratos

Esqueleto aprovado agora; não mover scripts funcionais nem criar motores concorrentes. Repositório compartilhado com Core 2; ferramentas independentes do runtime. Referência do estado consultado: 1aabd4e2f5139487c05ec1f8332182d939e91786. A Hyper 2.1 foi entregue separadamente; integração de seus arquivos requer ZIP/base real.

| Domínio | Responsabilidades / interfaces propostas | Reuso obrigatório |
|---|---|---|
| hyper_engine | simulation_kernel, clock, command_queue, randomness_service, spatial_index | experimental/apex2, kernel Hyper quando disponível, RaceRandomness |
| vehicle_dynamics | engine_model, gearbox, brakes, aero, tyres, integrator; SI | módulos race_longitudinal, performance, wet physics, KERS/DRS |
| racecraft | driver_agent, trajectory_planner, overtake_evaluator, defense_controller, traffic_predictor, incident_resolver | RaceSpace e módulos core de tráfego/erros |
| strategy | strategy_simulator, pit_window_predictor, weather_forecast, virtual_strategy_engineer, pit_crew_scheduler | Pit Wall, estratégia e double stack |
| engineering | component_registry, design_project, prototype_testing, production_scheduler, quality_control, supplier_contracts | inventário/oficina/garagem |
| career | world_simulator, championship_registry, driver_market, staff_market, financial_ledger, regulation_engine | carreira, contratos, saves |
| presentation | snapshot_adapter, renderer_3d, strategic_map_2d, broadcast_director, radio_system | HUD, câmera, rádio |
| quality_lab | integrity_monitor, benchmark_runner, scenario_generator, replay_validator, career_stress_test | FAST, tools/apex_lab_*, Lab externo |

Contrato esportivo: tick inteiro, seed, revisão, estado e comandos validados; saída snapshot somente leitura e eventos identificados. Agentes observam estado congelado e propõem intenções; solver é autoridade. RNG por domínio, não leitura de futuro. Não permitir que 3D altere resultados; 2D, TV e replay consomem snapshots. Saves com schema, migração e rollback; não mudar revisão antiga. 2012: V8, KERS, DRS, pneus e regras da época, sem cost cap moderno. Comando manual BOX V21 permanece soberano. Planejar módulos com entradas/saídas, unidades, ownership e critérios de aceite antes de criar arquivos GDScript. Proibir placeholders que se anunciem como funcionalidade real.

Infraestrutura de desenvolvimento existente: tools/apex_lab_architecture.py, apex_lab_graphics.py, apex_lab_release.py, apex_source_inventory.py, visual_regression_ab.py, apex_ci_tiers.py; workflow godot-setup.yml e APEX Test Lab. Usar esses mecanismos, não criar pipeline de CI concorrente. GPU física, TTS e reprodução visual requerem validação própria. FAST no SHA exato; FULL somente autorização explícita conforme AGENTS. Aprovado para preparar interfaces e registros agora, integração esportiva em incrementos.

Esqueleto operacional deste incremento: arquivos JSON versionados, IDs estáveis, registro de domínios, validação offline, contrato de asset e planejamento de jobs por hash. Não contém implementação nova dos 120 sistemas. A arquitetura é proposta, deve ser reconciliada com código existente antes de ligar módulos ao runtime.
