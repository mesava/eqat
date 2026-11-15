'use strict';

const $ = (id) => document.getElementById(id);
const statuses = {
  eligible_draft: 'В программе',
  pending_feature_confirmation: 'На уточнении',
  not_applicable: 'Вне профиля',
};
const sectionNames = {
  MLC: 'MLC', VMAT: 'VMAT и дуги', DOS: 'Дозиметрия', MEC: 'Механика', ACC: 'Аксессуары',
  IMG: 'Визуализация', HEX: 'HexaPOD', SAF: 'Безопасность', SGRT: 'SGRT и КТ', ABC: 'ABC',
};
const equipmentGroups = [
  ['Основные системы', ['agility_mlc', 'xvi', 'iviewgt', 'hexapod', 'catalyst', 'abc']],
  ['Клинические режимы', ['vmat', 'sliding_window', 'srs', 'sbrt', 'arc_rotation', 'dynamic_jaws']],
  ['Режимы визуализации', ['xvi_3d', 'xvi_static_2d', 'xvi_fluoroscopy', 'xvi_imaging_gating', 'laser_igrt_reference']],
  ['Дыхание и позиционирование', ['sgrt_gating', 'sgrt_rotated_couch', 'abc_automatic_interface', 'abc_at_ct', 'abc_distinct_units']],
  ['Аксессуары и оптика', ['electron_applicators', 'motorized_wedge', 'external_wedge', 'head_accessories',
    'dose_modifying_accessories', 'physical_graticule', 'crosshair_in_use', 'odi_in_use']],
];
const beamFields = [
  ['photon_energies', 'Фотоны', '6FF, 10FFF'],
  ['electron_energies_MeV', 'Электроны, МэВ', '6, 8, 10, 12, 15'],
];
const storageKey = 'eqat-profiles-v1';
let profiles = new Map();
let originals = new Map();
let labels = {};
let currentId;
let latest;
let requestNumber = 0;
let activeStatus = 'eligible_draft';

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function select(options, value) {
  const node = element('select');
  for (const [key, label] of options) node.add(new Option(label, key));
  node.value = value;
  return node;
}

function error(message) {
  $('error').hidden = !message;
  $('error').textContent = message;
}

function saveProfile(profile) {
  try {
    const saved = JSON.parse(localStorage.getItem(storageKey) || '{}');
    saved[profile.id] = profile;
    localStorage.setItem(storageKey, JSON.stringify(saved));
    return true;
  } catch {
    return false;
  }
}

function featureGroup(title, keys, profile, open) {
  const group = element('details', undefined, 'equipment-group');
  group.open = open;
  group.append(element('summary', title));
  for (const key of keys) {
    const field = element('label', labels[key], 'feature');
    const input = select([['unknown', 'Неизвестно'], ['present', 'Есть'], ['absent', 'Нет']],
      profile.features[key] || 'unknown');
    input.dataset.feature = key;
    field.append(input);
    group.append(field);
  }
  return group;
}

function beamGroup(profile) {
  const group = element('details', undefined, 'equipment-group');
  group.append(element('summary', 'Энергии пучков'));
  for (const [key, title, placeholder] of beamFields) {
    const values = profile[key];
    const field = element('label', title, 'feature');
    const mode = select([['unknown', 'Неизвестно'], ['listed', 'Список'], ['absent', 'Нет пучка']],
      Array.isArray(values) ? (values.length ? 'listed' : 'absent') : 'unknown');
    mode.dataset.beam = key;
    const input = element('input');
    input.id = `beam-${key}`;
    input.setAttribute('aria-label', `Энергии: ${title}`);
    input.placeholder = placeholder;
    input.value = values?.join(', ') || '';
    const sync = () => { input.hidden = mode.value !== 'listed'; input.required = !input.hidden; };
    mode.addEventListener('change', sync);
    sync();
    field.append(mode);
    group.append(field, input);
  }
  return group;
}

function showEquipment(profile) {
  const content = $('equipment');
  content.replaceChildren();
  if (profile.scope === 'ct') {
    content.append(featureGroup('КТ и дыхательная синхронизация', ['sentinel_ct', 'respiratory_4dct'], profile, true));
    return;
  }
  equipmentGroups.forEach(([title, keys], index) => content.append(featureGroup(title, keys, profile, index === 0)));
  content.append(beamGroup(profile));
}

function profileFromForm() {
  const profile = structuredClone(profiles.get(currentId));
  profile.display_name = $('profile-name').value.trim();
  profile.scope = $('scope').value;
  for (const field of $('equipment').querySelectorAll('[data-feature]')) {
    profile.features[field.dataset.feature] = field.value;
  }
  for (const field of $('equipment').querySelectorAll('[data-beam]')) {
    const key = field.dataset.beam;
    if (field.value === 'unknown') {
      delete profile[key];
    } else if (field.value === 'absent') {
      profile[key] = [];
    } else {
      let values = $(`beam-${key}`).value.split(/[,;\s]+/).filter(Boolean);
      if (key === 'electron_energies_MeV') values = values.map(Number);
      if (!values.length || (key === 'electron_energies_MeV' && values.some((n) => !Number.isFinite(n) || n <= 0))) {
        throw new Error('Укажите энергии пучков через запятую. Для электронов используйте числа в МэВ.');
      }
      profile[key] = [...new Set(values)];
    }
  }
  if (profile.scope === 'linac') profile.features.linac = 'present';
  return profile;
}

function activateProfile(id, calculateImmediately = true) {
  currentId = id;
  const profile = profiles.get(id);
  $('profiles').replaceChildren(...[...profiles].map(([key, value]) => new Option(value.display_name, key)));
  $('profiles').value = id;
  $('profile-name').value = profile.display_name;
  $('scope').value = profile.scope || 'linac';
  $('scope-field').hidden = originals.has(id);
  $('reset-profile').hidden = !originals.has(id);
  $('current-profile').textContent = profile.display_name;
  $('search').value = '';
  $('section').value = '';
  markDirty();
  showEquipment(profile);
  if (calculateImmediately) calculate(profile, false);
}

function markDirty() {
  requestNumber += 1;
  latest = undefined;
  $('download').disabled = true;
  $('calculate').disabled = false;
  $('profile-note').textContent = 'Примените профиль, чтобы обновить программу.';
  error('');
  draw();
}

async function calculate(profile, save) {
  const ticket = ++requestNumber;
  $('calculate').disabled = true;
  $('tests').setAttribute('aria-busy', 'true');
  $('profile-note').textContent = 'Подбор тестов…';
  error('');
  try {
    const response = await fetch('/api/program', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(profile),
    });
    const result = await response.json();
    if (ticket !== requestNumber) return;
    if (!response.ok) throw new Error(result.error);
    latest = result;
    profiles.set(profile.id, profile);
    $('profiles').selectedOptions[0].textContent = profile.display_name;
    $('current-profile').textContent = profile.display_name;
    $('download').disabled = false;
    const sections = [...new Set(result.program.machine_programs[0].items.map((item) => item.section))];
    const oldSection = $('section').value;
    $('section').replaceChildren(new Option('Все разделы', ''),
      ...sections.map((key) => new Option(sectionNames[key] || key, key)));
    $('section').value = sections.includes(oldSection) ? oldSection : '';
    $('profile-note').textContent = save ? (saveProfile(profile) ? 'Профиль сохранён в этом браузере.' :
      'Программа сформирована. Сохранение в браузере недоступно.') : '';
    draw();
  } catch (failure) {
    if (ticket !== requestNumber) return;
    $('profile-note').textContent = '';
    error(failure.message || 'Не удалось сформировать программу.');
  } finally {
    if (ticket === requestNumber) {
      $('calculate').disabled = false;
      $('tests').setAttribute('aria-busy', 'false');
    }
  }
}

function itemRow(item) {
  const row = element('details', undefined, 'test');
  row.dataset.code = item.test_code;
  const summary = element('summary');
  const info = element('span', undefined, 'test-info');
  info.append(element('span', item.name, 'test-name'),
    element('span', item.applicability_status === 'eligible_draft' ? item.frequency_text_unverified : item.reason,
      'test-description'));
  summary.append(element('span', item.test_code, 'test-code'), info);
  const content = element('dl', undefined, 'test-details');
  const fields = [
    ['Применимость', item.reason], ['Категория', item.category], ['Условия', item.applicability_details],
    ['Периодичность из каталога', item.frequency_text_unverified],
    ['Черновой критерий', item.acceptance_criterion_unapproved],
    ['Внеплановая проверка', item.post_service_text_unverified],
  ];
  for (const [label, value] of fields) {
    if (value) content.append(element('dt', label), element('dd', value));
  }
  row.append(summary, content);
  return row;
}

function draw() {
  const machine = latest?.program.machine_programs[0];
  $('included-count').textContent = machine ? machine.summary.eligible_draft || 0 : '—';
  $('pending-count').textContent = machine ? machine.summary.pending_feature_confirmation || 0 : '—';
  $('excluded-count').textContent = machine ? machine.summary.not_applicable || 0 : '—';
  $('tests').setAttribute('aria-busy', 'false');
  const query = $('search').value.trim().toLocaleLowerCase('ru');
  const section = $('section').value;
  const rows = machine?.items.filter((item) => item.applicability_status === activeStatus &&
    (!section || section === item.section) && `${item.test_code} ${item.name}`.toLocaleLowerCase('ru').includes(query));
  $('visible-count').textContent = rows ? `${rows.length} / ${machine.summary[activeStatus] || 0}` : '';
  $('tests').replaceChildren(...(rows?.length ? rows.map(itemRow) : [element('p',
    machine ? 'По этим фильтрам тестов нет.' : 'Сформируйте программу по выбранному профилю.', 'empty')]));
}

$('profile-form').addEventListener('submit', (event) => {
  event.preventDefault();
  try {
    const profile = profileFromForm();
    if (!profile.display_name) throw new Error('Укажите название профиля.');
    calculate(profile, true);
  } catch (failure) {
    error(failure.message);
  }
});
$('profile-form').addEventListener('input', markDirty);
$('scope').addEventListener('change', () => showEquipment({ ...profiles.get(currentId), scope: $('scope').value }));
$('profiles').addEventListener('change', () => activateProfile($('profiles').value));
$('reset-profile').addEventListener('click', () => {
  const original = structuredClone(originals.get(currentId));
  profiles.set(currentId, original);
  saveProfile(original);
  activateProfile(currentId);
});
$('new-profile').addEventListener('click', () => {
  const profile = { id: `local-${crypto.randomUUID()}`, display_name: 'Новая установка', scope: 'linac', features: {} };
  profiles.set(profile.id, profile);
  activateProfile(profile.id, false);
  $('profile-name').focus();
  $('profile-name').select();
});
for (const button of document.querySelectorAll('[data-state]')) {
  button.addEventListener('click', () => {
    activeStatus = button.dataset.state;
    for (const item of document.querySelectorAll('[data-state]')) {
      item.setAttribute('aria-pressed', String(item === button));
    }
    draw();
  });
}
$('section').addEventListener('change', draw);
$('search').addEventListener('input', draw);
$('download').addEventListener('click', () => {
  if (!latest) return;
  const url = URL.createObjectURL(new Blob([latest.markdown], { type: 'text/markdown;charset=utf-8' }));
  const link = element('a');
  link.href = url;
  link.download = `EQAT-${currentId.replace(/[^a-z0-9_-]/gi, '_')}.md`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});

async function initialize() {
  const response = await fetch('/api/setup');
  if (!response.ok) throw new Error('Профили недоступны. Перезапустите рабочее место EQAT.');
  const setup = await response.json();
  labels = setup.labels;
  originals = new Map(setup.profiles.map((profile) => [profile.id, profile]));
  profiles = new Map(originals);
  try {
    const saved = JSON.parse(localStorage.getItem(storageKey) || '{}');
    for (const profile of Object.values(saved)) {
      if (profile?.id && profile.display_name && profile.features) profiles.set(profile.id, profile);
    }
  } catch {
    $('profile-note').textContent = 'Сохранённые профили недоступны.';
  }
  $('profiles').disabled = false;
  $('new-profile').disabled = false;
  activateProfile(setup.profiles[0].id);
}

initialize().catch((failure) => {
  $('tests').setAttribute('aria-busy', 'false');
  $('current-profile').textContent = 'Профили недоступны';
  error(failure.message);
});
