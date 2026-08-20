/* ==========================================================================
   The Break Room — Pokémon battle (GBA SP edition)
   Live stats & sprites via the free PokeAPI (pokeapi.co). No ROMs here.
   ========================================================================== */

(function () {
    'use strict';

    const root = document.getElementById('battle-root');
    if (!root) return;

    const SPRITES = 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-iii/ruby-sapphire';
    const API = 'https://pokeapi.co/api/v2/pokemon';

    // --------------------------------------------------------------
    // Roster: iconic movesets curated, stats fetched live
    // --------------------------------------------------------------
    const ROSTER = [
        { id: 25,  name: 'Pikachu',    types: ['electric'],         moves: [['Thunderbolt','electric',90],['Iron Tail','steel',100],['Quick Attack','normal',40],['Thunder','electric',110]] },
        { id: 6,   name: 'Charizard',  types: ['fire','flying'],    moves: [['Flamethrower','fire',90],['Air Slash','flying',75],['Dragon Claw','dragon',80],['Fire Blast','fire',110]] },
        { id: 9,   name: 'Blastoise',  types: ['water'],            moves: [['Hydro Pump','water',110],['Surf','water',90],['Ice Beam','ice',90],['Bite','dark',60]] },
        { id: 3,   name: 'Venusaur',   types: ['grass','poison'],   moves: [['Solar Beam','grass',120],['Sludge Bomb','poison',90],['Razor Leaf','grass',55],['Earthquake','ground',100]] },
        { id: 94,  name: 'Gengar',     types: ['ghost','poison'],   moves: [['Shadow Ball','ghost',80],['Sludge Bomb','poison',90],['Psychic','psychic',90],['Dark Pulse','dark',80]] },
        { id: 65,  name: 'Alakazam',   types: ['psychic'],          moves: [['Psychic','psychic',90],['Shadow Ball','ghost',80],['Energy Ball','grass',90],['Focus Blast','fighting',120]] },
        { id: 68,  name: 'Machamp',    types: ['fighting'],         moves: [['Cross Chop','fighting',100],['Earthquake','ground',100],['Rock Slide','rock',75],['Fire Punch','fire',75]] },
        { id: 59,  name: 'Arcanine',   types: ['fire'],             moves: [['Flare Blitz','fire',120],['Extreme Speed','normal',80],['Crunch','dark',80],['Wild Charge','electric',90]] },
        { id: 38,  name: 'Ninetales',  types: ['fire'],             moves: [['Flamethrower','fire',90],['Solar Beam','grass',120],['Dark Pulse','dark',80],['Extrasensory','psychic',80]] },
        { id: 131, name: 'Lapras',     types: ['water','ice'],      moves: [['Surf','water',90],['Ice Beam','ice',90],['Thunderbolt','electric',90],['Body Slam','normal',85]] },
        { id: 91,  name: 'Cloyster',   types: ['water','ice'],      moves: [['Ice Beam','ice',90],['Hydro Pump','water',110],['Rock Blast','rock',75],['Poison Jab','poison',80]] },
        { id: 130, name: 'Gyarados',   types: ['water','flying'],   moves: [['Waterfall','water',80],['Crunch','dark',80],['Hurricane','flying',110],['Ice Fang','ice',65]] },
        { id: 149, name: 'Dragonite',  types: ['dragon','flying'],  moves: [['Dragon Claw','dragon',80],['Hurricane','flying',110],['Thunder Punch','electric',75],['Extreme Speed','normal',80]] },
        { id: 143, name: 'Snorlax',    types: ['normal'],           moves: [['Body Slam','normal',85],['Earthquake','ground',100],['Crunch','dark',80],['Hyper Beam','normal',150]] },
        { id: 150, name: 'Mewtwo',     types: ['psychic'],          moves: [['Psystrike','psychic',100],['Aura Sphere','fighting',80],['Shadow Ball','ghost',80],['Ice Beam','ice',90]] },
        { id: 151, name: 'Mew',        types: ['psychic'],          moves: [['Psychic','psychic',90],['Flamethrower','fire',90],['Thunderbolt','electric',90],['Ice Beam','ice',90]] },
        { id: 133, name: 'Eevee',      types: ['normal'],           moves: [['Double-Edge','normal',120],['Bite','dark',60],['Swift','normal',60],['Quick Attack','normal',40]] },
        { id: 135, name: 'Jolteon',    types: ['electric'],         moves: [['Thunderbolt','electric',90],['Thunder','electric',110],['Shadow Ball','ghost',80],['Quick Attack','normal',40]] },
        { id: 134, name: 'Vaporeon',   types: ['water'],            moves: [['Surf','water',90],['Ice Beam','ice',90],['Shadow Ball','ghost',80],['Aqua Tail','water',90]] },
        { id: 136, name: 'Flareon',    types: ['fire'],             moves: [['Flare Blitz','fire',120],['Superpower','fighting',120],['Bite','dark',60],['Quick Attack','normal',40]] },
        { id: 123, name: 'Scyther',    types: ['bug','flying'],     moves: [['X-Scissor','bug',80],['Aerial Ace','flying',60],['Night Slash','dark',70],['Slash','normal',70]] },
        { id: 142, name: 'Aerodactyl', types: ['rock','flying'],    moves: [['Stone Edge','rock',100],['Earthquake','ground',100],['Crunch','dark',80],['Aerial Ace','flying',60]] },
        { id: 95,  name: 'Onix',       types: ['rock','ground'],    moves: [['Stone Edge','rock',100],['Earthquake','ground',100],['Iron Tail','steel',100],['Crunch','dark',80]] },
        { id: 121, name: 'Starmie',    types: ['water','psychic'],  moves: [['Surf','water',90],['Psychic','psychic',90],['Thunderbolt','electric',90],['Ice Beam','ice',90]] }
    ];

    // Partial type chart: CHART[attacking][defending] = multiplier (default 1)
    const CHART = {
        fire:     { grass: 2, ice: 2, steel: 2, bug: 2, fire: 0.5, water: 0.5, rock: 0.5, dragon: 0.5 },
        water:    { fire: 2, ground: 2, rock: 2, water: 0.5, grass: 0.5, dragon: 0.5 },
        grass:    { water: 2, ground: 2, rock: 2, fire: 0.5, grass: 0.5, poison: 0.5, flying: 0.5, dragon: 0.5, steel: 0.5, bug: 0.5 },
        electric: { water: 2, flying: 2, electric: 0.5, grass: 0.5, dragon: 0.5, ground: 0 },
        ice:      { grass: 2, ground: 2, flying: 2, dragon: 2, fire: 0.5, water: 0.5, ice: 0.5, steel: 0.5 },
        fighting: { normal: 2, ice: 2, rock: 2, dark: 2, steel: 2, poison: 0.5, flying: 0.5, psychic: 0.5, bug: 0.5, ghost: 0 },
        poison:   { grass: 2, poison: 0.5, ground: 0.5, rock: 0.5, ghost: 0.5, steel: 0 },
        ground:   { fire: 2, electric: 2, poison: 2, rock: 2, steel: 2, grass: 0.5, bug: 0.5, flying: 0 },
        flying:   { grass: 2, fighting: 2, bug: 2, electric: 0.5, rock: 0.5, steel: 0.5 },
        psychic:  { fighting: 2, poison: 2, psychic: 0.5, steel: 0.5, dark: 0 },
        ghost:    { psychic: 2, ghost: 2, dark: 0.5, normal: 0 },
        dragon:   { dragon: 2, steel: 0.5 },
        dark:     { psychic: 2, ghost: 2, fighting: 0.5, dark: 0.5 },
        steel:    { ice: 2, rock: 2, fire: 0.5, water: 0.5, electric: 0.5, steel: 0.5 },
        bug:      { grass: 2, psychic: 2, dark: 2, fire: 0.5, fighting: 0.5, flying: 0.5, ghost: 0.5, poison: 0.5, steel: 0.5 },
        rock:     { fire: 2, ice: 2, flying: 2, bug: 2, fighting: 0.5, ground: 0.5, steel: 0.5 },
        normal:   { rock: 0.5, steel: 0.5, ghost: 0 }
    };

    const FX = {
        fire: '🔥', water: '💧', grass: '🍃', electric: '⚡', ice: '❄️', psychic: '🌀',
        ghost: '👻', dragon: '🐉', dark: '🌑', normal: '💥', flying: '🌪️', fighting: '👊',
        poison: '☠️', ground: '🪨', rock: '🪨', steel: '⚙️', bug: '🐛'
    };

    const statCache = new Map();

    async function getStats(id) {
        if (statCache.has(id)) return statCache.get(id);
        try {
            const res = await fetch(`${API}/${id}`);
            const data = await res.json();
            const s = (n) => data.stats.find(x => x.stat.name === n)?.base_stat ?? 80;
            const stats = { hp: s('hp'), atk: Math.max(s('attack'), s('special-attack')), def: (s('defense') + s('special-defense')) / 2, spd: s('speed') };
            statCache.set(id, stats);
            return stats;
        } catch (e) {
            return { hp: 80, atk: 85, def: 80, spd: 80 };
        }
    }

    function maxHP(base) { return Math.floor(base * 2 + 110); }

    function calcDamage(attacker, defender, move) {
        const [, type, power] = move;
        let mult = 1;
        defender.types.forEach(t => { mult *= (CHART[type] && CHART[type][t] !== undefined) ? CHART[type][t] : 1; });
        const stab = attacker.types.includes(type) ? 1.5 : 1;
        const rand = 0.85 + Math.random() * 0.15;
        const dmg = Math.floor((((2 * 50 / 5 + 2) * power * (attacker.stats.atk / defender.stats.def)) / 50 + 2) * stab * mult * rand);
        return { dmg: Math.max(1, dmg), mult };
    }

    // --------------------------------------------------------------
    // State
    // --------------------------------------------------------------
    let player = null;
    let enemy = null;
    let busy = false;
    let mode = 'select'; // select | battle | over

    // --------------------------------------------------------------
    // Screens
    // --------------------------------------------------------------
    function selectScreen() {
        busy = false;
        mode = 'select';
        player = null;
        enemy = null;
        root.innerHTML = `
            <div class="battle-select">
                <div class="battle-title">CHOOSE YOUR POKÉMON</div>
                <div class="select-grid">
                    ${ROSTER.map((p, i) => `
                        <button class="select-mon" data-i="${i}">
                            <img src="${SPRITES}/${p.id}.png" alt="${p.name}" loading="lazy">
                            <span>${p.name.toUpperCase()}</span>
                        </button>`).join('')}
                </div>
            </div>`;
        root.querySelectorAll('.select-mon').forEach(btn => {
            btn.addEventListener('click', () => startBattle(Number(btn.dataset.i)));
        });
    }

    async function startBattle(playerIdx) {
        root.innerHTML = '<div class="battle-loading">A challenger approaches…</div>';
        mode = 'battle';

        let enemyIdx = Math.floor(Math.random() * ROSTER.length);
        if (enemyIdx === playerIdx) enemyIdx = (enemyIdx + 1 + Math.floor(Math.random() * (ROSTER.length - 1))) % ROSTER.length;

        const [pStats, eStats] = await Promise.all([getStats(ROSTER[playerIdx].id), getStats(ROSTER[enemyIdx].id)]);

        player = { ...ROSTER[playerIdx], stats: pStats, hp: maxHP(pStats.hp), max: maxHP(pStats.hp) };
        enemy  = { ...ROSTER[enemyIdx],  stats: eStats, hp: maxHP(eStats.hp), max: maxHP(eStats.hp) };

        root.innerHTML = `
            <div class="battle-scene">
                <div class="battle-row enemy-row">
                    <div class="gba-statbox">
                        <div class="gba-name">${enemy.name.toUpperCase()} <span class="gba-lv">Lv50</span></div>
                        <div class="gba-hp-row"><span class="hp-label">HP</span><div class="hp-track"><div class="hp-fill" id="enemy-hp" style="width:100%"></div></div></div>
                    </div>
                    <div class="mon-stage enemy-stage">
                        <div class="platform"></div>
                        <img class="mon-sprite enemy-sprite" id="enemy-sprite" src="${SPRITES}/${enemy.id}.png" alt="${enemy.name}">
                    </div>
                </div>
                <div class="battle-row player-row">
                    <div class="mon-stage player-stage">
                        <div class="platform platform-near"></div>
                        <img class="mon-sprite player-sprite" id="player-sprite" src="${SPRITES}/back/${player.id}.png" alt="${player.name}">
                    </div>
                    <div class="gba-statbox">
                        <div class="gba-name">${player.name.toUpperCase()} <span class="gba-lv">Lv50</span></div>
                        <div class="gba-hp-row"><span class="hp-label">HP</span><div class="hp-track"><div class="hp-fill" id="player-hp" style="width:100%"></div></div></div>
                        <div class="hp-num" id="player-hp-num">${player.hp}/${player.max}</div>
                    </div>
                </div>
            </div>
            <div class="gba-textbox" id="battle-log">A wild ${enemy.name.toUpperCase()} appeared!<span class="tb-caret">▼</span></div>
            <div class="move-grid" id="move-grid">
                ${player.moves.map((m, i) => `
                    <button class="move-btn" data-i="${i}">
                        <span class="move-name">${m[0]}</span>
                        <span class="move-meta">${m[1].toUpperCase()} ${m[2]}</span>
                    </button>`).join('')}
            </div>`;

        root.querySelectorAll('.move-btn').forEach(btn => {
            btn.addEventListener('click', () => playerTurn(Number(btn.dataset.i)));
        });
    }

    const log = (msg) => {
        const el = document.getElementById('battle-log');
        if (el) el.innerHTML = `${msg}<span class="tb-caret">▼</span>`;
    };

    function setHP(who) {
        const key = who === player ? 'player' : 'enemy';
        const bar = document.getElementById(`${key}-hp`);
        const num = document.getElementById(`${key}-hp-num`);
        const pct = Math.max(0, who.hp / who.max * 100);
        if (bar) { bar.style.width = pct + '%'; bar.classList.toggle('low', pct < 25); bar.classList.toggle('mid', pct >= 25 && pct < 55); }
        if (num) num.textContent = `${Math.max(0, who.hp)}/${who.max}`;
    }

    function animateAttack(attacker, defender, moveType) {
        const atkEl = document.getElementById(attacker === player ? 'player-sprite' : 'enemy-sprite');
        const defStage = document.querySelector(defender === player ? '.player-stage' : '.enemy-stage');
        const defEl = document.getElementById(defender === player ? 'player-sprite' : 'enemy-sprite');

        if (atkEl) {
            atkEl.classList.remove('lunge-right', 'lunge-left');
            void atkEl.offsetWidth;
            atkEl.classList.add(attacker === player ? 'lunge-right' : 'lunge-left');
        }

        window.setTimeout(() => {
            if (defStage) {
                const fx = document.createElement('span');
                fx.className = 'battle-fx fx-' + moveType;
                fx.textContent = FX[moveType] || '💥';
                defStage.appendChild(fx);
                window.setTimeout(() => fx.remove(), 620);
            }
            if (defEl) {
                defEl.classList.remove('hit');
                void defEl.offsetWidth;
                defEl.classList.add('hit');
            }
        }, 260);
    }

    function effText(mult) {
        if (mult === 0) return " It doesn't affect the target…";
        if (mult >= 2) return " It's super effective!";
        if (mult < 1) return " It's not very effective…";
        return '';
    }

    async function playerTurn(moveIdx) {
        if (busy || mode !== 'battle' || !player || !enemy) return;
        busy = true;
        setMoves(false);

        const first = player.stats.spd >= enemy.stats.spd ? 'player' : 'enemy';
        const order = first === 'player'
            ? [attackAs(player, enemy, moveIdx), attackAs(enemy, player)]
            : [attackAs(enemy, player), attackAs(player, enemy, moveIdx)];

        for (const turn of order) {
            const done = await turn();
            if (done) return;
        }

        busy = false;
        setMoves(true);
    }

    function attackAs(attacker, defender, moveIdx) {
        return async function () {
            const move = moveIdx !== undefined ? attacker.moves[moveIdx] : attacker.moves[Math.floor(Math.random() * attacker.moves.length)];
            const { dmg, mult } = calcDamage(attacker, defender, move);
            log(`${attacker.name.toUpperCase()} used ${move[0].toUpperCase()}!`);
            animateAttack(attacker, defender, move[1]);
            await wait(750);
            defender.hp -= mult === 0 ? 0 : dmg;
            setHP(defender);
            log(`${attacker.name.toUpperCase()} used ${move[0].toUpperCase()}!${effText(mult)}`);
            await wait(850);
            if (defender.hp <= 0) { endBattle(defender === enemy); return true; }
            return false;
        };
    }

    function setMoves(enabled) {
        root.querySelectorAll('.move-btn').forEach(b => { b.disabled = !enabled; });
    }

    function endBattle(playerWon) {
        mode = 'over';
        const grid = document.getElementById('move-grid');
        if (playerWon) {
            log(`${enemy.name.toUpperCase()} fainted! You win!`);
            goldConfetti();
        } else {
            log(`${player.name.toUpperCase()} fainted! The house wins this round…`);
        }
        if (grid) {
            grid.innerHTML = `<button class="move-btn rematch" id="rematch">${playerWon ? '🏆 BATTLE AGAIN' : '↻ REMATCH'}</button>`;
            document.getElementById('rematch').addEventListener('click', selectScreen);
        }
        busy = false;
    }

    function goldConfetti() {
        const bits = ['🪙', '✨', '⭐'];
        for (let i = 0; i < 30; i++) {
            const b = document.createElement('span');
            b.className = 'confetti-bit';
            b.textContent = bits[Math.floor(Math.random() * bits.length)];
            b.style.left = Math.random() * 100 + 'vw';
            b.style.animationDelay = Math.random() * 0.7 + 's';
            b.style.fontSize = (0.9 + Math.random() * 1.2) + 'rem';
            document.body.appendChild(b);
            setTimeout(() => b.remove(), 4200);
        }
    }

    const wait = (ms) => new Promise(r => setTimeout(r, ms));

    // --------------------------------------------------------------
    // A / B buttons on the shell
    // --------------------------------------------------------------
    const btnA = document.getElementById('gba-a');
    const btnB = document.getElementById('gba-b');

    if (btnA) btnA.addEventListener('click', () => {
        if (mode === 'select') {
            startBattle(Math.floor(Math.random() * ROSTER.length));
        } else if (mode === 'battle' && !busy && player) {
            playerTurn(Math.floor(Math.random() * player.moves.length));
        } else if (mode === 'over') {
            selectScreen();
        }
    });

    if (btnB) btnB.addEventListener('click', () => {
        if (mode !== 'select' && !busy) selectScreen();
    });

    // Boot
    selectScreen();

})();
