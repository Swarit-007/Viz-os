"""Virtual memory: page replacement, Belady's anomaly, working set, TLB translation, two-level page tables."""

import random
from typing import Any, Dict, List

from ..core import Choice, Int, IntList, Trace, algorithm, result, tile

# REFS is the classic reference string (FIFO 15 faults, LRU 12, Optimal 9 with 3 frames).
# BELADY is the string that makes FIFO fault MORE with 4 frames (10) than with 3 (9).
REFS = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1]
BELADY = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]


# Random reference string with some locality (a page is often a repeat of a recent one), so policies differ visibly.
def _random_refs(rng, length=None):
    length = length or rng.randint(14, 22)
    span = rng.randint(4, 8)
    refs: List[int] = []
    for i in range(length):
        refs.append(refs[i - rng.randint(1, 3)] if i > 2 and rng.random() < 0.35 else rng.randint(0, span))
    return refs


# --------------------------------------------------------------------------- page replacement engine
# One engine for all six replacement policies. `slots` is the physical frames; each request is either a hit
# (page already resident) or a fault, and on a fault with no free frame `policy` chooses a victim.
# Bookkeeping per page: loaded_at (for FIFO), last_used (LRU/MRU), freq (LFU), and reference bits + a hand (Clock).
# Returns one step dict per request plus the total fault count.
def simulate_replacement(policy: str, frames: int, refs: List[int]):
    """Returns (steps, faults). Slots keep their frame position, like a textbook table."""
    slots: List[Any] = [None] * frames
    loaded_at: Dict[int, int] = {}
    last_used: Dict[int, int] = {}
    freq: Dict[int, int] = {}
    ref_bit = [0] * frames
    hand = 0
    steps, faults = [], 0
    for i, page in enumerate(refs):
        step = {'page': page, 'hit': page in slots, 'evicted': None, 'slot': None, 'why': ''}
        if step['hit']:
            slot = slots.index(page)
            step['slot'] = slot
            ref_bit[slot] = 1
        else:
            faults += 1
            if None in slots:
                slot = slots.index(None)
            else:
                if policy == 'fifo':
                    victim = min(slots, key=lambda x: loaded_at[x])
                    step['why'] = f'{victim} was loaded first'
                elif policy == 'lru':
                    victim = min(slots, key=lambda x: last_used[x])
                    step['why'] = f'{victim} was used longest ago'
                elif policy == 'mru':
                    victim = max(slots, key=lambda x: last_used[x])
                    step['why'] = f'{victim} was used most recently'
                elif policy == 'lfu':
                    victim = min(slots, key=lambda x: (freq[x], loaded_at[x]))
                    step['why'] = f'{victim} was used least often ({freq[victim]}x)'
                # Optimal looks at the FUTURE of the reference string: evict the page used farthest away (or never again).
                elif policy == 'optimal':
                    future = refs[i + 1:]
                    victim = max(slots, key=lambda x: future.index(x) if x in future else len(refs) + 1)
                    step['why'] = f'{victim} is not needed again' if victim not in future else f'{victim} is needed farthest in the future'
                # Clock: sweep the hand around the frames. A page with reference bit 1 gets a second chance (bit cleared);
                # the first page found with bit 0 is the victim.
                else:  # clock
                    while ref_bit[hand]:
                        ref_bit[hand] = 0
                        hand = (hand + 1) % frames
                    victim = slots[hand]
                    step['why'] = f'the hand found {victim} with reference bit 0'
                slot = slots.index(victim)
                step['evicted'] = victim
                if policy == 'clock':
                    hand = (slot + 1) % frames
            slots[slot] = page
            loaded_at[page] = i
            freq[page] = 0
            ref_bit[slot] = 1
            step['slot'] = slot
        last_used[page] = i
        freq[page] = freq.get(page, 0) + 1
        step['slots'] = list(slots)
        if policy == 'clock':
            step['refbits'] = list(ref_bit)
            step['hand'] = hand
        steps.append(step)
    return steps, faults


VICTIM_TEXT = {'fifo': 'evict the page that has been resident longest', 'lru': 'evict the page unused for the longest time',
               'mru': 'evict the page used most recently', 'lfu': 'evict the page used least often (oldest on a tie)',
               'optimal': 'evict the page whose next use is farthest away', 'clock': 'sweep the hand, clearing reference bits, evict the first with bit 0'}
HIT_TEXT = {'lru': ' (record the use time)', 'mru': ' (record the use time)', 'lfu': ' (count the use)', 'clock': ' (set its reference bit)',
            'fifo': '', 'optimal': ''}
NOTES = {
    'fifo': ['Cheap, but ignores how often a page is used.', 'Can suffer Belady\'s anomaly: more frames may cause more faults.'],
    'lru': ['Approximates the optimal policy by assuming the past predicts the future.', 'Never suffers Belady\'s anomaly (a stack algorithm).'],
    'mru': ['The opposite of LRU: good for cyclic scans larger than memory, poor for ordinary locality.'],
    'lfu': ['Keeps popular pages, but old popular pages linger after they go cold.'],
    'optimal': ['Belady\'s MIN: needs the future, so it is only a yardstick.', 'No policy can have fewer faults.'],
    'clock': ['Second chance: a circular list with reference bits, the practical approximation of LRU.', 'The hand moves only when a fault needs a victim.'],
}
LABELS = {'fifo': 'FIFO', 'lru': 'LRU', 'mru': 'MRU', 'lfu': 'LFU', 'optimal': 'Optimal', 'clock': 'Clock'}


# Factory: register one algorithm per policy so each has its own pseudocode, summary and notes.
def _replacement(policy):
    pseudo = ['for each page request:', '    if the page is in a frame: HIT' + HIT_TEXT[policy], '    else: PAGE FAULT',
              '        if a frame is free: use it', '        else: ' + VICTIM_TEXT[policy], '        load the page into the frame']

    def run(p):
        steps, faults = simulate_replacement(policy, p['frames'], p['refs'])
        trace = Trace()
        for i, s in enumerate(steps):
            if s['hit']:
                trace.add(f'Request {s["page"]}: it is already in frame {s["slot"] + 1}. Hit.', [0, 1], i)
            elif s['evicted'] is None:
                trace.add(f'Request {s["page"]}: page fault. Frame {s["slot"] + 1} is free, so load it there.', [0, 2, 3, 5], i)
            else:
                trace.add(f'Request {s["page"]}: page fault. No free frame: {s["why"]}. Page {s["evicted"]} leaves frame {s["slot"] + 1}.', [0, 2, 4, 5], i)
        total = len(p['refs'])
        summary = [tile('Page faults', faults, tone='bad'), tile('Hits', total - faults, tone='good'),
                   tile('Hit ratio', f'{(total - faults) / total * 100:.1f}%'), tile('Fault ratio', f'{faults / total * 100:.1f}%')]
        return result(f'page-{policy}', 'frames', summary, trace, {'frames': p['frames'], 'refs': p['refs'], 'steps': steps, 'clock': policy == 'clock'})

    algorithm(id=f'page-{policy}', name=f'{LABELS[policy]} Page Replacement', category='paging', family='page',
              summary={'fifo': 'Evict the page that has been in memory the longest.', 'lru': 'Evict the page that has gone unused the longest.',
                       'mru': 'Evict the page that was used most recently.', 'lfu': 'Evict the page used the fewest times.',
                       'optimal': 'Evict the page that will not be needed for the longest time. Needs the future.',
                       'clock': 'Circular list with reference bits: give recently used pages a second chance.'}[policy],
              viz='frames', complexity={'time': 'O(refs x frames)', 'space': 'O(frames)', 'note': ''}, pseudocode=pseudo,
              params=[Int('frames', 'Frames', 3, 1, 10), IntList('refs', 'Reference string', REFS, 0, 99, 1, 60)],
              example={'frames': 3, 'refs': REFS}, random=lambda rng: {'frames': rng.randint(3, 4), 'refs': _random_refs(rng)},
              notes=NOTES[policy], tags=['page replacement'])(run)


for _p in LABELS:
    _replacement(_p)


# --------------------------------------------------------------------------- Belady's anomaly and working set
@algorithm(id='belady', name='Belady\'s Anomaly', category='paging', viz='curve', family='belady',
           summary='More frames should mean fewer faults. For FIFO, sometimes it does not. Plot faults against frames.',
           complexity={'time': 'O(frames x refs x frames)', 'space': 'O(frames)', 'note': ''},
           pseudocode=['for f = 1 to max frames:', '    faults[f] = run the policy with f frames', 'plot faults against f',
                       'an anomaly is any f where faults[f+1] > faults[f]'],
           params=[IntList('refs', 'Reference string', BELADY, 0, 99, 1, 60), Int('max_frames', 'Largest frame count', 7, 2, 12)],
           example={'refs': BELADY, 'max_frames': 7}, random=lambda rng: {'refs': _random_refs(rng), 'max_frames': 7},
           notes=['The classic string 1 2 3 4 1 2 5 1 2 3 4 5 gives FIFO 9 faults with 3 frames and 10 with 4.',
                  'LRU and Optimal are stack algorithms and never show the anomaly.'], tags=['page replacement'])
# Run FIFO, LRU and Optimal for every frame count from 1 to max_frames and plot faults against frames.
# A FIFO point that is higher than the one before it is Belady's anomaly.
def belady(p):
    xs = list(range(1, p['max_frames'] + 1))
    series = [{'label': LABELS[pol], 'y': [simulate_replacement(pol, f, p['refs'])[1] for f in xs]} for pol in ('fifo', 'lru', 'optimal')]
    trace = Trace()
    anomalies = []
    for i, f in enumerate(xs):
        note = f'{f} frame(s): ' + ', '.join(f'{s["label"]} {s["y"][i]}' for s in series) + ' faults.'
        if i and series[0]['y'][i] > series[0]['y'][i - 1]:
            anomalies.append(f)
            note += f' FIFO got worse than with {f - 1} frame(s): Belady\'s anomaly!'
        trace.add(note, [0, 1, 2], i)
    summary = [tile('FIFO anomaly', 'yes' if anomalies else 'no', f'at {anomalies[0]} frames' if anomalies else None, 'bad' if anomalies else 'good'),
               tile('Best at largest size', min(s['y'][-1] for s in series))]
    verdict = {'ok': not anomalies, 'label': 'Anomaly found' if anomalies else 'No anomaly',
               'text': f'FIFO faults rise when frames grow to {anomalies[0]}.' if anomalies else 'Faults never rise with more frames for this string.'}
    return result('belady', 'curve', summary, trace, {'x': xs, 'series': series, 'xLabel': 'Frames', 'yLabel': 'Page faults',
                                                      'mark': anomalies}, None, verdict)


@algorithm(id='working-set', name='Working Set Model', category='paging', viz='curve', family='ws',
           summary='How many distinct pages did a process touch in its last Δ references? Too few frames means thrashing.',
           complexity={'time': 'O(refs x window)', 'space': 'O(window)', 'note': ''},
           pseudocode=['for each time t:', '    window = the last delta references up to t', '    working set = the distinct pages in window',
                       '    demand = size of the working set', 'if total demand > frames: swap a process out (avoid thrashing)'],
           params=[IntList('refs', 'Reference string', [1, 2, 1, 3, 1, 2, 4, 4, 4, 5, 6, 5, 6, 5, 6, 1, 2, 3, 1, 2], 0, 99, 1, 60),
                   Int('window', 'Window Δ', 4, 1, 20)],
           example={'refs': [1, 2, 1, 3, 1, 2, 4, 4, 4, 5, 6, 5, 6, 5, 6, 1, 2, 3, 1, 2], 'window': 4},
           random=lambda rng: {'refs': _random_refs(rng, 24), 'window': rng.randint(3, 6)},
           notes=['A program moves through phases (localities); its working set size rises and falls with them.'], tags=['thrashing'])
# Working set W(t, delta) = the distinct pages referenced in the last `delta` references up to time t.
# Its size over time shows program phases; a process needs about that many frames to avoid thrashing.
def working_set(p):
    refs, w = p['refs'], p['window']
    sizes, sets = [], []
    trace = Trace()
    for t in range(len(refs)):
        ws = sorted(set(refs[max(0, t - w + 1):t + 1]))
        sizes.append(len(ws))
        sets.append(ws)
        trace.add(f't={t + 1}: page {refs[t]} referenced. Last {min(w, t + 1)} refs give working set {{{", ".join(map(str, ws))}}}, size {len(ws)}.', [1, 2, 3], t)
    summary = [tile('Peak working set', max(sizes)), tile('Average', f'{sum(sizes) / len(sizes):.2f}'), tile('Window Δ', w)]
    table = {'title': 'Working set over time', 'headers': ['t', 'Page', 'Working set', 'Size'],
             'rows': [[t + 1, refs[t], '{' + ', '.join(map(str, sets[t])) + '}', sizes[t]] for t in range(len(refs))]}
    return result('working-set', 'curve', summary, trace, {'x': list(range(1, len(refs) + 1)), 'series': [{'label': 'Working set size', 'y': sizes}],
                                                            'xLabel': 'Time', 'yLabel': 'Pages', 'mark': [], 'refs': refs}, table)


# --------------------------------------------------------------------------- TLB translation
@algorithm(id='tlb', name='Address Translation with a TLB', category='paging', viz='translate', family='translate',
           summary='Split a virtual address into page and offset, try the TLB, fall back to the page table, and compute effective access time.',
           complexity={'time': 'O(accesses x tlb size)', 'space': 'O(pages)', 'note': ''},
           pseudocode=['page = address / page size; offset = address % page size', 'look the page up in the TLB',
                       'hit: frame comes straight from the TLB', 'miss: read the page table in memory', 'if the page is not in memory: page fault, load it',
                       'insert the mapping into the TLB (evict the oldest if full)', 'physical address = frame x page size + offset'],
           params=[Choice('page_size', 'Page size', [(str(s), str(s)) for s in (256, 512, 1024, 4096)], '1024'),
                   IntList('page_table', 'Page table (frame per page, -1 = not in memory)', [5, 2, -1, 7, 1, -1], -1, 99, 1, 16),
                   IntList('addresses', 'Virtual addresses', [100, 300, 2100, 2200, 1030, 1100, 100, 2300], 0, 65535, 1, 30),
                   Int('tlb_size', 'TLB entries', 2, 1, 8), Int('t_tlb', 'TLB time (ns)', 10, 0, 100), Int('t_mem', 'Memory time (ns)', 100, 1, 1000)],
           example={'page_size': '1024', 'page_table': [5, 2, -1, 7, 1, -1], 'addresses': [100, 300, 2100, 2200, 1030, 1100, 100, 2300],
                    'tlb_size': 2, 't_tlb': 10, 't_mem': 100},
           random=lambda rng: {'page_size': '1024', 'page_table': [rng.choice([-1, rng.randint(0, 9)]) for _ in range(6)],
                               'addresses': [rng.randint(0, 6143) for _ in range(8)], 'tlb_size': rng.randint(1, 4), 't_tlb': 10, 't_mem': 100},
           notes=['effective access time = h x (t_tlb + t_mem) + (1 - h) x (t_tlb + 2 x t_mem), ignoring page-fault service time.',
                  'Locality is why a tiny TLB works so well.'], tags=['tlb', 'paging'])
# Translate virtual addresses: page = address // page_size, offset = address % page_size.
# Look in the TLB first (a small cache of recent page -> frame mappings). On a miss read the page table in memory;
# if the page is not resident that is a page fault and the OS loads it into a fresh frame. Finally
# physical address = frame * page_size + offset.
# Effective access time (EAT) blends the fast TLB-hit path and the slower two-memory-access miss path.
def tlb(p):
    size = int(p['page_size'])
    table = list(p['page_table'])
    tlb_entries: List[Dict[str, int]] = []
    trace, accesses, hits, faults = Trace(), [], 0, 0
    next_frame = max(table + [-1]) + 1
    for i, va in enumerate(p['addresses']):
        page, off = divmod(va, size)
        row = {'va': va, 'page': page, 'offset': off, 'tlb': 'miss', 'fault': False, 'frame': None, 'pa': None, 'invalid': False}
        if page >= len(table):
            row['invalid'] = True
            accesses.append({**row, 'tlbAfter': [dict(e) for e in tlb_entries], 'note': f'Page {page} is outside the address space: segmentation fault.'})
            trace.add(f'Address {va}: page {page} does not exist (the table has {len(table)} pages). Invalid access.', [0], i)
            continue
        lines = [0, 1]
        hit = next((e for e in tlb_entries if e['page'] == page), None)
        if hit:
            hits += 1
            row.update(tlb='hit', frame=hit['frame'])
            note = f'Address {va} = page {page}, offset {off}. TLB hit: frame {hit["frame"]}.'
            lines += [2, 6]
        else:
            lines.append(3)
            if table[page] < 0:
                faults += 1
                table[page] = next_frame
                next_frame += 1
                row['fault'] = True
                lines.append(4)
            row['frame'] = table[page]
            if len(tlb_entries) >= p['tlb_size']:
                tlb_entries.pop(0)
            tlb_entries.append({'page': page, 'frame': table[page]})
            lines += [5, 6]
            note = (f'Address {va} = page {page}, offset {off}. TLB miss. ' + (f'Page fault: page loaded into frame {table[page]}. ' if row['fault'] else f'Page table gives frame {table[page]}. '))
        row['pa'] = row['frame'] * size + off
        note += f' Physical address = {row["frame"]} x {size} + {off} = {row["pa"]}.'
        accesses.append({**row, 'tlbAfter': [dict(e) for e in tlb_entries], 'tableAfter': list(table), 'note': note})
        trace.add(note, lines, i)
    valid = [a for a in accesses if not a['invalid']]
    ratio = hits / len(valid) if valid else 0
    eat = ratio * (p['t_tlb'] + p['t_mem']) + (1 - ratio) * (p['t_tlb'] + 2 * p['t_mem'])
    summary = [tile('TLB hit ratio', f'{ratio * 100:.1f}%'), tile('Effective access time', f'{eat:.1f} ns'),
               tile('Page faults', faults, tone='bad' if faults else None), tile('Without a TLB', f'{2 * p["t_mem"]} ns')]
    return result('tlb', 'translate', summary, trace, {'pageSize': size, 'accesses': accesses, 'tlbSize': p['tlb_size'], 'pages': len(table),
                                                        'initialTable': list(p['page_table'])})


# --------------------------------------------------------------------------- two-level page table
@algorithm(id='two-level', name='Two-level Page Table', category='paging', viz='multilevel', family='translate',
           summary='Split the page number into an outer and an inner index. Inner tables exist only for regions in use, saving memory.',
           complexity={'time': 'O(accesses)', 'space': 'O(used regions)', 'note': ''},
           pseudocode=['split the address into outer index, inner index, offset', 'outer table[outer index] names an inner table',
                       'if there is none yet: allocate one', 'inner table[inner index] holds the frame number (allocate on first touch)',
                       'physical address = frame x page size + offset'],
           params=[Int('bits_outer', 'Outer index bits', 4, 1, 8), Int('bits_inner', 'Inner index bits', 4, 1, 8), Int('bits_offset', 'Offset bits', 8, 1, 12),
                   IntList('addresses', 'Virtual addresses', [0x0123, 0x0456, 0x0F23, 0x8123, 0x8124, 0xC777, 0x0125], 0, 1 << 20, 1, 24)],
           example={'bits_outer': 4, 'bits_inner': 4, 'bits_offset': 8, 'addresses': [0x0123, 0x0456, 0x0F23, 0x8123, 0x8124, 0xC777, 0x0125]},
           random=lambda rng: {'bits_outer': 4, 'bits_inner': 4, 'bits_offset': 8, 'addresses': [rng.choice([0, 0x4000, 0x8000, 0xC000]) + rng.randint(0, 0x3FFF) for _ in range(8)]},
           notes=['A single-level table for this address space would need every entry allocated; two levels allocate only what is touched.'], tags=['page table'])
# The virtual address is cut into [outer index | inner index | offset]. The outer table points to inner tables,
# which are created only the first time a region is touched. That is the whole point: sparse address spaces
# need far fewer table entries than one giant single-level table.
def two_level(p):
    bo, bi, bf = p['bits_outer'], p['bits_inner'], p['bits_offset']
    total = bo + bi + bf
    inners: Dict[int, Dict[int, int]] = {}
    next_frame, trace, accesses = 0, Trace(), []
    for i, va in enumerate(p['addresses']):
        va &= (1 << total) - 1
        off = va & ((1 << bf) - 1)
        i2 = (va >> bf) & ((1 << bi) - 1)
        i1 = va >> (bf + bi)
        new_inner = i1 not in inners
        if new_inner:
            inners[i1] = {}
        new_page = i2 not in inners[i1]
        if new_page:
            inners[i1][i2] = next_frame
            next_frame += 1
        frame = inners[i1][i2]
        pa = (frame << bf) | off
        note = (f'Address 0x{va:0{(total + 3) // 4}X}: outer {i1}, inner {i2}, offset {off}. '
                + ('Allocate a new inner table. ' if new_inner else 'Inner table already exists. ')
                + (f'First touch: frame {frame} assigned. ' if new_page else f'Frame {frame}. ') + f'Physical address 0x{pa:X}.')
        accesses.append({'va': va, 'outer': i1, 'inner': i2, 'offset': off, 'frame': frame, 'pa': pa, 'newInner': new_inner, 'newPage': new_page,
                         'innerTables': sorted(inners), 'note': note})
        trace.add(note, [0, 1] + ([2] if new_inner else []) + [3, 4], i)
    single = 1 << (bo + bi)
    two = (1 << bo) + len(inners) * (1 << bi)
    summary = [tile('Single-level entries', single), tile('Two-level entries', two), tile('Inner tables', f'{len(inners)}/{1 << bo}'),
               tile('Saved', f'{(1 - two / single) * 100:.0f}%', tone='good' if two < single else None)]
    return result('two-level', 'multilevel', summary, trace, {'bitsOuter': bo, 'bitsInner': bi, 'bitsOffset': bf, 'accesses': accesses,
                                                              'outerSize': 1 << bo, 'innerSize': 1 << bi})
