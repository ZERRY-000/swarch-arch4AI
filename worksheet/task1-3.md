# Tutorial 6 worksheet: serving patterns

**Name / ชื่อ:**

**Student ID / รหัสนิสิต:**

This is **individual work**: each student completes and submits their own copy, in their own fork.

*งานนี้เป็น**งานเดี่ยว** นิสิตแต่ละคนทำและส่งงานของตัวเอง โดยใช้ forked repository ของตัวเอง*

Copy result rows from `results/runs.csv` (or the load test's output) into the tables. Keep answers short: one to three sentences each. Answer in Thai or English.

ตอนที่ตอบ ให้นิสิตคัดลอกผลจาก `results/runs.csv` (หรือจาก output ของ load test) ลงในตาราง ตอบสั้นๆ ข้อละ 1–3 ประโยค จะตอบเป็นภาษาไทยหรือภาษาอังกฤษก็ได้

## Task 0: Baseline (copy the baseline results from `results/runs.csv` here / copy ผลลัพธ์ของ baseline จาก `results/runs.csv` มาวางที่นี่)

| Run | p50 ms | p95 ms | accuracy | large calls |
|---|---|---|---|---|
| t0-large | 512 | 623 | 93.5% | 100% |
| t0-small | 32 | 119 | 72.5% | 0% |

**Q0.** What does the large model buy, and what does it cost?

*large model ให้อะไรเพิ่ม และต้องแลกด้วยอะไร*

> large model ทำให้ accuracy สูงขึ้นจาก 72.5% (t0-small) เป็น 93.5% (t0-large) ซึ่งผ่าน QR3 (≥ 90%) ส่วน small model ไม่ผ่าน แต่ต้องแลกกับ latency ที่สูงกว่ามาก (p50 512 ms เทียบกับ 32 ms และ p95 623 ms เทียบกับ 119 ms) และค่าใช้จ่าย เพราะทุกรีวิว (100%) ถูกส่งไป large model ซึ่งมีค่าใช้จ่ายทุก call และรับได้สูงสุดแค่ 20 calls/s

## Task 1: Fallback prediction (copy the Task 1 results from `results/runs.csv` here / copy ผลลัพธ์ของ Task 1 จาก `results/runs.csv` มาวางที่นี่)

| Run | run time (s) | p50 ms | p95 ms | errors | pending | accuracy |
|---|---|---|---|---|---|---|
| t1-before | 30.3 | 253 | 431 | 21 | 0 | 92.7% |
| t1-after | 9.9 | 419 | 1011 | 0 | 24 | 92.6% |

**Q1.1** In `t1-before`, p50 can look *better* than the baseline. Why is p50 misleading here? Which column tells the real story?

*ใน `t1-before` ค่า p50 อาจดู "ดีกว่า" baseline ทำไม p50 จึงทำให้เข้าใจผิดในกรณีนี้ และ column ไหนบอกความจริง*

> p50 ของ t1-before (253 ms) คำนวณจาก request ที่ได้คำตอบเท่านั้น ส่วน 21 request ที่ค้างจนเกิน 10 s ถูกนับเป็น errors และไม่ถูกนำมาคิด latency เลย นอกจากนี้ request ที่ค้างอยู่ยังกินช่อง concurrency ของ client ทำให้ request ที่เหลือแย่ง large model กันน้อยลงและดูเร็วขึ้น column ที่บอกความจริงคือ `errors` (21 จาก 200 หรือประมาณ 10.5%) และ run time ที่เพิ่มจาก 10.4 s เป็น 30.3 s

**Q1.2** The hang affects only 10% of large-model calls. Why is it worse for the system than 10% of reviews being slow? Think about what a waiting request holds on to in the review service and the gateway.

*การค้างเกิดกับ calls ไปยัง large model แค่ 10% ทำไมจึงส่งผลต่อระบบแย่กว่าการที่รีวิว 10% ช้าลงเฉยๆ ลองคิดว่า request ที่รออยู่ถือทรัพยากรอะไรไว้ใน review service และ gateway*

> request ที่ค้างไม่ได้แค่ช้า แต่ยังถือทรัพยากรไว้ตลอดเวลาที่รอ ได้แก่ connection, coroutine/worker ใน review service และ gateway รวมถึงช่อง concurrency ของ client ทำให้ request อื่นที่ปกติต้องรอคิวตามไปด้วย (resource exhaustion และ cascading failure) ผลคือ throughput ของทั้งระบบลดลง run time จึงเพิ่มขึ้นเกือบ 3 เท่า (10.4 s เป็น 30.3 s ใน t1-before) แม้ว่ามีแค่ 10% ของ calls ที่ค้าง

**Q1.3** Pending reviews have no label. Suggest what should happen to them, and name the topology from the lecture that does it.

*รีวิวที่ pending ยังไม่มี label ควรจัดการกับรีวิวเหล่านี้อย่างไร และ topology ใดจาก lecture ที่ทำแบบนั้น*

> ควรเก็บรีวิวที่ pending ไว้ (ไม่ทิ้ง ตาม FR4) แล้วนำเข้าคิวหรือให้ batch job ดึงรีวิวที่ status = pending มาส่งให้ inference service ติด label ใหม่ภายหลัง เมื่อ large model กลับมาปกติ โดยมี retry และ backoff ซึ่งตรงกับ topology แบบ **Asynchronous / batch (T4)** ที่รีวิวเข้าคิว (broker) หรือถูกเก็บไว้ แล้วถูก score ทีหลังเป็นชุด

**Q1.4** We chose a 1-second timeout. What goes wrong if it is 0.1 s? And if it is 10 s?

*เราเลือก timeout 1 วินาที จะเกิดปัญหาอะไรถ้าตั้งเป็น 0.1 วินาที และถ้าตั้งเป็น 10 วินาที*

> ถ้าใช้ 0.1 s จะสั้นกว่าเวลาปกติของ large model (~200 ms และ p50 ภายใต้โหลดประมาณ 500 ms ใน t0-large) ทำให้ call ที่ปกติดีก็ timeout เกือบทั้งหมด รีวิวเกือบทุกอันจึงกลายเป็น pending และยังเสียค่า large call ไปฟรีๆ ถ้าใช้ 10 s จะเท่ากับ client timeout (10 s) ทำให้ client ยอมแพ้ก่อน fallback จะทำงาน errors จึงกลับมา และ request ที่ค้างยังถือทรัพยากรไว้นานเหมือนกรณี t1-before ซึ่งผิด QR1 และ QR2 (ที่กำหนดให้รอไม่เกิน 1 s)

## Task 2: Cascade (copy the Task 2 results from `results/runs.csv` here / copy ผลลัพธ์ของ Task 2 จาก `results/runs.csv` มาวางที่นี่)

| Run | threshold | p50 ms | p95 ms | accuracy | large calls |
|---|---|---|---|---|---|
| t2-0.6 | 0.6 | 7 | 562 | 91.5% | 38% |
| t2-0.7 | 0.7 | 374 | 604 | 93.0% | 53% |
| t2-0.8 | 0.8 | 494 | 696 | 93.5% | 64% |
| t2-0.9 | 0.9 | 476 | 614 | 93.5% | 77% |

**Q2.1** Which threshold would you deploy for CampusEats, and why? Name the quality you give up.

*จะเลือก threshold ใดสำหรับ deploy ใน CampusEats เพราะอะไร และต้องยอมเสีย quality ใดไป*

> เลือก **0.7**: accuracy 93.0% ผ่าน QR3 โดยมี margin 3 percentage points และลด large calls เหลือ 53% (ลดลง 47% จาก t0-large) ขณะที่ 0.8 และ 0.9 เพิ่ม accuracy แค่ 0.5 percentage points แต่ใช้ large model 64% และ 77% ส่วน 0.6 ถูกที่สุด (38%) แต่ได้ 91.5% ซึ่งเหลือ margin แค่ 1.5 percentage points จากตัวอย่าง 200 รีวิว (1 รีวิว = 0.5%) จึงเสี่ยงหลุด QR3 quality ที่ยอมเสียคือ **cost** (QR4: จ่ายค่า large calls มากกว่า 0.6 อีก 15 percentage points) และ p50 latency ที่สูงกว่า 0.6 มาก (374 ms เทียบกับ 7 ms)

**Q2.2** Look at p50 and p95 for your threshold. Why does the cascade help p50 much more than p95?

*ดูค่า p50 และ p95 ของ threshold ที่เลือก ทำไม cascade จึงช่วย p50 ได้มากกว่า p95 มาก*

> cascade ทำให้รีวิวที่ง่ายจบที่ small model ภายในไม่กี่ ms แต่รีวิวที่ยากยังต้องไป large model เหมือนเดิม (บวกเวลาของ small model อีกเล็กน้อย) และ p95 ถูกกำหนดโดยรีวิวกลุ่มที่ช้าที่สุดเสมอ ซึ่งก็คือรีวิวที่ไป large model ดังนั้น p95 จึงลดลงเพียงเล็กน้อย (623 ms เป็น 604 ms) จากการที่คิวของ large model สั้นลง สำหรับ threshold 0.7 มีถึง 53% ที่ไป large model ซึ่งเกินครึ่ง p50 จึงยังเป็น large call (374 ms) ส่วนที่ 0.6 ซึ่งไป large แค่ 38% ค่า p50 ลดลงเหลือ 7 ms

**Q2.3** The cascade trusts the small model's confidence. Give one situation where that trust is misplaced, and its effect on users.

*cascade เชื่อ confidence ของ small model ยกตัวอย่างหนึ่งสถานการณ์ที่ไม่ควรเชื่อ และผลที่เกิดกับผู้ใช้*

> small model เป็น bag of words จาก 100 คำ จึงอาจ confident ผิดกับประโยคประชดหรือปฏิเสธ เช่น "Wow, never showed up on time. Amazing service." ซึ่งมีคำว่า amazing และ wow ทำให้ทาย positive ด้วย confidence สูงจนไม่ถูกส่งต่อไป large model ผลคือรีวิวเชิงลบถูกติด label positive เจ้าของร้านจึงไม่เห็นลูกค้าที่ไม่พอใจ (ซึ่งเป็นเป้าหมายหลักของระบบ) และลูกค้าที่บ่นก็รู้สึกว่าไม่มีใครฟัง

## Task 3: Cached predictions (copy the Task 3 results from `results/runs.csv` here / copy ผลลัพธ์ของ Task 3 จาก `results/runs.csv` มาวางที่นี่)

| Run | p50 ms | p95 ms | accuracy | large calls | cache hits |
|---|---|---|---|---|---|
| t3-cache | 8 | 582 | 93.0% | 38% | 35% |

**Q3.1** Which reviews benefit from the cache, and which never will?

*รีวิวแบบไหนได้ประโยชน์จาก cache และแบบไหนไม่มีวันได้ประโยชน์*

> รีวิวที่ข้อความซ้ำกัน (หลังจากแปลงเป็นตัวพิมพ์เล็กและตัดช่องว่าง) ได้ประโยชน์ โดยเฉพาะรีวิวสั้นๆ ที่พบบ่อย เช่น "Delicious!", "Too salty", "Yummy" ซึ่งเป็นประมาณ 25% ของ workload ใน t3-cache cache_hits = 35% ทำให้ large calls ลดจาก 53% เหลือ 38% และ p50 ลดจาก 374 ms เหลือ 8 ms ส่วนรีวิวที่ยาวและไม่ซ้ำ (unique) จะไม่มีวันได้ประโยชน์ เพราะครั้งแรกเป็น miss เสมอ และข้อความที่ต่างกันแม้แต่เครื่องหมายวรรคตอนก็เป็นคนละ key

**Q3.2** Next week you deploy a better large model. What must happen to the cache, and how would you design for it?

*สัปดาห์หน้าจะ deploy large model ตัวใหม่ที่ดีกว่าเดิม ต้องทำอะไรกับ cache และจะออกแบบรองรับเรื่องนี้อย่างไร*

> cache ที่เก็บคำตอบของ model เก่าจะ stale จึงต้อง invalidate ไม่อย่างนั้นผู้ใช้จะยังได้คำตอบจาก model เก่าแม้ deploy model ใหม่แล้ว ควรออกแบบให้ cache key รวม model version (เช่น `(model_version, threshold, normalised_text)`) เมื่อ deploy version ใหม่ entry เก่าจะไม่ถูกใช้และค่อยๆ ถูก LRU evict ออกไปเอง อาจเพิ่ม TTL และระวังว่าหลัง deploy ใหม่ hit rate จะเป็น 0 ทำให้ large calls พุ่งขึ้นชั่วคราว (cold cache) จึงควรวางแผน capacity หรือ warm cache ล่วงหน้าด้วยรีวิวที่พบบ่อย

## Debrief

**Q4.** Name one thing you learned from these measurements that the lecture did not cover.

*ยกตัวอย่างหนึ่งสิ่งที่ได้เรียนรู้จากการวัดผลครั้งนี้ ที่ไม่มีพูดถึงใน lecture*

> percentile ไม่ได้เปลี่ยนแบบเส้นตรงตาม threshold: p50 กระโดดจาก 7 ms (t2-0.6) เป็น 374 ms (t2-0.7) เพียงเพราะสัดส่วน large calls ข้ามจาก 38% ไปเกิน 50% และในทางกลับกัน การแก้ปัญหาที่ถูกต้อง (t1-after) กลับทำให้ p95 ดูแย่ลง (431 ms เป็น 1011 ms) เพราะ request ที่เคยหายไปเป็น errors ตอนนี้ถูกนับ latency ด้วย จึงต้องดู errors, pending และ run time คู่กับ latency เสมอ
