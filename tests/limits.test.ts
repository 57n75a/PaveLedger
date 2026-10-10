import test from 'node:test';import assert from 'node:assert/strict';
import {bodyTooLarge,MAX_BODY,MAX_IMAGE_BODY,IMAGE_ACTIONS} from '../lib/limits.ts';

test('ordinary requests keep the small limit',()=>{assert.equal(bodyTooLarge(500,'transition'),false);assert.equal(bodyTooLarge(MAX_BODY,'create'),false);assert.equal(bodyTooLarge(MAX_BODY+1,'create'),true);assert.equal(bodyTooLarge(200_000,'transition'),true);assert.equal(bodyTooLarge(200_000,undefined),true);assert.equal(bodyTooLarge(200_000,{}),true)});
test('image actions may carry a resized image',()=>{for(const a of IMAGE_ACTIONS){assert.equal(bodyTooLarge(MAX_BODY+1,a),false,a);assert.equal(bodyTooLarge(450_000,a),false,a);assert.equal(bodyTooLarge(MAX_IMAGE_BODY,a),false,a)}});
test('nothing may exceed the overall cap, even for image actions',()=>{for(const a of [...IMAGE_ACTIONS,'create',undefined])assert.equal(bodyTooLarge(MAX_IMAGE_BODY+1,a),true,String(a))});
test('exactly the five image-carrying actions are listed',()=>{assert.deepEqual([...IMAGE_ACTIONS].sort(),['branding','contract','contractUpdate','selfProfile','teamUpdate'])});
test('the largest stored image still fits in one request with room to spare',()=>{const biggestStored=450_000;assert.ok(biggestStored+2_000<MAX_IMAGE_BODY);assert.ok(MAX_IMAGE_BODY<4_500_000)});
