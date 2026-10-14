import {test} from 'node:test';
import assert from 'node:assert/strict';
import {toCyrillic} from '../lib/cyrillic.ts';

test('transliterates Serbian including digraphs', () => {
  assert.equal(toCyrillic('Održavanje puteva'), 'Одржавање путева');
  assert.equal(toCyrillic('Ljubljanska, Njegoševa, džep, DŽ'), 'Љубљанска, Његошева, џеп, Џ');
  assert.equal(toCyrillic('Đorđe Čačić'), 'Ђорђе Чачић');
});

test('keeps codes, acronyms, brands, Roman numerals, emails and addresses in Latin', () => {
  assert.equal(toCyrillic('Kralja Petra I'), 'Краља Петра I');
  assert.equal(toCyrillic('RS-DEMO-003 · Preuzmi PDF'), 'RS-DEMO-003 · Преузми PDF');
  assert.equal(toCyrillic('PaveLedger Srbija'), 'PaveLedger Србија');
  assert.equal(toCyrillic('Pišite na marko@putevi-uzice.rs'), 'Пишите на marko@putevi-uzice.rs');
  assert.equal(toCyrillic('Otvori u Google mapama'), 'Отвори у Google мапама');
  assert.equal(toCyrillic('PL-2026-AB12CD34'), 'PL-2026-AB12CD34');
});
