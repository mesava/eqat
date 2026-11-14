# Результаты аудита / границы верификации

Дата 2026-11-10. Аудит **исходной пользовательской книги** и предыдущей матрицы.

## Подтверждённые количественные результаты
- 71 лист в исходной книге.
- 10 реестров, 161 уникальный код.
- 104 исходные строки кратких SOP (часть описывает несколько тестов).
- 138 кодов упомянуты отдельными или групповыми SOP.
- 23 кода без отдельной/групповой записи SOP.
- Среди 138: у восьми тестов MLC отсутствует отдельно заполненный столбец «Анализ (из Excel)». Шаги и критерии в других столбцах присутствуют; это не означает отсутствия анализа вообще.
- Для всех 161 есть текст исходного источника и ссылка на хотя бы один документ в предварительной матрице, но **проверка точной редакции и раздела для каждого кода НЕ завершена**.
- 35 полей FullPackage сохранены как отдельный диагностический набор, а не новые периодические тесты.

## Восемь SOP с незаполненным отдельным блоком анализа
`MLC-W1`, `MLC-M1`, `MLC-M2`, `MLC-M3`, `MLC-A1`, `MLC-A2`, `MLC-A3`, `MLC-X1`.

## 23 пробела, требующие редакторской задачи
| Код | Тест | Кандидат на общую процедуру |
|---|---|---|
| `MLC-D1` | Упрощённая проверка положения MLC перед SRS | Создать отдельную SOP; кандидат для связи: MLC-W1 (адаптировать специально для SRS) |
| `VMAT-M4` | Комплексный референсный VMAT-план: точечная доза и распределение | Создать отдельную SOP; кандидат для связи: MLC-M1 (физически общий тест) |
| `VMAT-S2` | Полный Elekta VMAT eCAT и успешная доставка H&N_VMATCAT | Создать отдельную SOP; кандидат для связи: VMAT-S1 + VMAT eCAT (отдельный vendor workflow) |
| `DOS-M2` | Ежемесячное постоянство профиля / OAF | Создать отдельную SOP; кандидат для связи: DOS-D1 / D2 (дополнить ежемесячную процедуру) |
| `DOS-A9` | Выход фотонов в зависимости от дозовой мощности | Создать отдельную SOP; кандидат для связи: VMAT-A1 (физически общий тест) |
| `DOS-Q1` | Перекрёстная проверка QA-приборов и референсных систем | Создать отдельную SOP; кандидат для связи: DOS-D1/D2 + DOS-M1 (cross-calibration independent SOP) |
| `MEC-M5` | Физическая гратикула портальной плёнки | Создать отдельную SOP; кандидат для связи: MEC-M6 (дополнить проверку гратикулы) |
| `MEC-S1` | Механический isocenter и crosswire locus по Elekta CAT | Создать отдельную SOP; кандидат для связи: MEC-A4 (нужен отдельный service/CAT SOP) |
| `ACC-M2` | Точность установки внешнего физического клина и его лотка | Создать отдельную SOP; кандидат для связи: ACC-A4 (неполный аналог — отдельный SOP) |
| `ACC-U1` | Проверка электронного аппликатора перед каждым применением | Создать отдельную SOP; кандидат для связи: ACC-A3 (создать отдельный SOP перед каждым применением) |
| `IMG-D3` | Imaging-treatment isocenter при использовании лазеров как treatment reference | Создать отдельную SOP; кандидат для связи: IMG-D2 (отдельный laser-reference маршрут) |
| `IMG-A8` | Imaging gating interlock | Создать отдельную SOP; кандидат для связи: IMG-D1 (отдельный imaging gating interlock SOP) |
| `IMG-E1` | End-to-end IGRT geometry | Создать отдельную SOP; кандидат для связи: IMG-D2 + HEX-A2 (оформить E2E) |
| `HEX-Q2` | Ортогональность и cross-coupling | Создать отдельную SOP; кандидат для связи: HEX-M3 (дополнить cross-coupling) |
| `HEX-A1` | Полный годовой диапазон 6DoF | Создать отдельную SOP; кандидат для связи: HEX-M1/M2/M3 (дополнить полный диапазон 6DoF) |
| `SAF-D9` | Beam enable при корректной конфигурации | Создать отдельную SOP; кандидат для связи: SAF-D6 (отдельный beam-enable checklist) |
| `SAF-M1` | Полный функциональный охват Emergency OFF | Создать отдельную SOP; кандидат для связи: SAF-D4/D5 (полный охват E-stop) |
| `SAF-M5` | Imaging beam and motion safety interlocks | Создать отдельную SOP; кандидат для связи: IMG-D1 (imaging-specific interlocks) |
| `SAF-M6` | Couch motion limits и механические soft limits | Создать отдельную SOP; кандидат для связи: MEC-L1 / L2 (couch safety limits) |
| `SAF-A5` | Safety labels, инструкции и физическая доступность | Создать отдельную SOP; кандидат для связи: SAF-A1 (добавить маркировку и доступность) |
| `SGRT-M6` | ROI и устойчивость регистрации | Создать отдельную SOP; кандидат для связи: SGRT-M1 (ROI/registration robustness отдельным SOP) |
| `SGRT-A7` | System integrity и физическая фиксация камер | Создать отдельную SOP; кандидат для связи: SGRT-A1 (camera mounting integrity отдельным SOP) |
| `ABC-A2` | Полный range/flow calibration и environmental check | Создать отдельную SOP; кандидат для связи: ABC-Q1 (расширенная calibration range) |

## Документальные spot checks
Сверены названия и наличие релевантных тем/разделов в текстах выбранных документов из пользовательского Drive. Это *не* утверждение, что численные критерии и годовые/месячные интервалы в Excel совпадают с каждым первоисточником.

| Тест | Источник | Найденный раздел / тема | Уровень подтверждения |
|---|---|---|---|
| `VMAT-M2` | VMAT eCAT | 3.3.4 Picket Fence test with variable dose rate / PF G0VDR | matching_section_found_in_extracted_document |
| `VMAT-M3` | VMAT eCAT | 3.3.2 Diaphragm abutment / D Abut | matching_section_found_in_extracted_document |
| `IMG-M5`, `IMG-A2` | XVI eCAT | TOR 18FG Leeds and 1 mm copper plate | matching_procedure_found_in_extracted_document |
| `IMG-M3`, `IMG-A3` | XVI eCAT | Catphan CTP503 / CTP600 | matching_equipment_found_in_extracted_document |
| `IMG-M4` | iViewGT eCAT | 3.1 Doing the image quality test | matching_section_found_in_extracted_document |
| `SGRT-D3` | Catalyst IFU | daily QA / выполнение стандартной процедуры QA | matching_section_found_in_extracted_document |
| `ABC-D3` | ABC eCAT | balloon valve and volume threshold / timer | matching_procedure_found_in_extracted_document |
| `HEX-A3` | iGUIDE IFU | HexaPOD iGUIDE 2.2 IFU (1052558) | document_identity_checked_only |
| `MLC-W1` | MPPG 8.b | MLC leaf position accuracy (section to confirm) | topic_found_in_extracted_document |
| `MEC-A4` | TG-198 | isocenter and mechanical QA (section to confirm) | document_present_and_topic_confirmed |

## Что ещё необходимо проверить построчно
1. Сравнить каждую заявленную формулу/частоту/численный критерий Excel с конкретным **разделом и страницей** документа, а не только с заголовком.
2. Зафиксировать источники как локальные нормативные требования, рекомендации AAPM, заводские acceptance tests либо исследовательские методы. Эти классы имеют разный статус.
3. Проверить применимость используемых Elekta eCAT/IFU к установленным версиям Integrity, XVI 5.0.6, iGUIDE, Catalyst.
4. Сверить методики для малых полей, FFF, 6DoF и SRS с реальным оснащением.
5. Выполнить клиническую валидацию после поступления измерений (на текущий момент их нет).
6. Оценить конфликты и исключённые тесты, а также дополнительные правила программы вне десяти реестров.

## Предостережение
Текстовые ссылки на документы и примерная связь по тематике НЕ являются доказательством совпадения допусков. Все критерии экспорта помечены `UNAPPROVED_DRAFT`.
