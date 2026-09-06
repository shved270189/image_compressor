async (page) => {
  const results = [];
  const downloads = [];
  const onDownload = (download) => downloads.push(download);
  page.on('download', onDownload);
  const check = (condition, name) => {
    if (!condition) throw new Error(name);
    results.push(name);
  };
  const fixture = '/tmp/image-download-feasibility/chrome-immediate.png';
  await page.addInitScript(() => {
    if (window.probeResources) return;
    const active = new Set();
    const create = URL.createObjectURL.bind(URL);
    const revoke = URL.revokeObjectURL.bind(URL);
    window.probeResources = { active };
    URL.createObjectURL = (blob) => {
      const url = create(blob);
      active.add(url);
      return url;
    };
    URL.revokeObjectURL = (url) => { active.delete(url); revoke(url); };
  });
  try {
    await page.goto('http://127.0.0.1:8765');
    for (const mode of ['immediate', 'task', 'retain']) {
      await page.locator('#release').selectOption(mode);
      for (let repeat = 0; repeat < 2; repeat++) {
        await page.locator('#file').setInputFiles(fixture);
        await page.locator('#preview').waitFor({ state: 'visible' });
        await page.locator('#width').fill('500');
        const pending = page.waitForEvent('download');
        await page.getByRole('button', { name: 'Process probe', exact: true }).click();
        const download = await pending;
        const saved = `/tmp/image-download-feasibility/${download.suggestedFilename()}`;
        await download.saveAs(saved);
        check(await download.failure() === null, `${mode}/${repeat}: download completes`);
        check(await page.locator('#status').textContent() === 'Empty', `${mode}/${repeat}: reset`);
        check(await page.locator('#file').inputValue() === '', `${mode}/${repeat}: native input cleared`);
        check(await page.locator('#width').inputValue() === '', `${mode}/${repeat}: bounds cleared`);
        const before = await page.locator('#log').textContent();
        await page.locator('#verify').setInputFiles(saved);
        await page.waitForFunction((prior) => {
          const log = document.querySelector('#log').textContent;
          return log !== prior && JSON.parse(log).events.at(-1).startsWith('verification ');
        }, before);
        check(JSON.parse(await page.locator('#log').textContent()).events.at(-1).startsWith('verification PASS'), `${mode}/${repeat}: current downloaded bytes and dimensions verified`);
        await page.locator('#replay').click();
        if (mode === 'retain') await page.locator('#cleanup').click();
        check(await page.evaluate(() => window.probeResources.active.size) === 0, `${mode}/${repeat}: no active object URLs after handoff`);
      }
    }
    check(downloads.length === 6, 'six submissions produce six downloads; replay does not download');
    for (const scenario of ['failure', 'truncated']) {
      await page.locator('#scenario').selectOption(scenario);
      await page.locator('#file').setInputFiles(fixture);
      await page.locator('#width').fill('500');
      await page.locator('#submit').click();
      await page.waitForFunction(() => document.querySelector('#status').textContent.startsWith('Retry:'));
      check(await page.locator('#width').inputValue() === '500', `${scenario}: parameters retained`);
      check(await page.locator('#preview').isVisible(), `${scenario}: Preview retained`);
      check(await page.locator('#submit').isEnabled(), `${scenario}: retry enabled`);
      check(await page.evaluate(() => window.probeResources.active.size) === 1, `${scenario}: only the current Preview URL remains`);
    }
    await page.locator('#scenario').selectOption('slow');
    await page.locator('#release').selectOption('immediate');
    const pending = page.waitForEvent('download', { timeout: 15000 });
    await page.locator('#submit').click();
    check(await page.locator('#file').isDisabled(), 'busy: selection locked');
    check(await page.locator('#width').isDisabled(), 'busy: parameters locked');
    await page.locator('#form').evaluate((form) => {
      form.dispatchEvent(new Event('submit', { cancelable: true }));
    });
    const delayed = await pending;
    await delayed.saveAs('/tmp/image-download-feasibility/chrome-delayed.png');
    check(await delayed.failure() === null, 'delayed response: complete download');
    check(downloads.length === 7, 'busy duplicate submission ignored');
    await page.locator('#file').setInputFiles(fixture);
    const beforeInvalidation = JSON.parse(await page.locator('#log').textContent()).events.length;
    await page.locator('#submit').click();
    await page.locator('#invalidate').click();
    await page.waitForFunction((offset) => JSON.parse(document.querySelector('#log').textContent)
      .events.slice(offset).includes('obsolete completion ignored'), beforeInvalidation, { timeout: 15000 });
    check(downloads.length === 7, 'invalidated delayed completion does not download');
    check(await page.locator('#status').textContent() === 'Empty', 'invalidated completion does not restore form');
    await page.locator('#file').setInputFiles(fixture);
    await page.locator('#submit').click();
    check(await page.evaluate(() => {
      dispatchEvent(new Event('pagehide'));
      return window.probeResources.active.size;
    }) === 0, 'pagehide handler releases all object URLs');
    await page.reload();
    check(await page.locator('#status').textContent() === 'Empty', 'reload restores neither input nor result');
    await page.waitForTimeout(8500);
    check(downloads.length === 7, 'reload cancels pending operation without download');
    const closingPage = await page.context().newPage();
    try {
      await closingPage.goto('http://127.0.0.1:8765');
      await closingPage.locator('#file').setInputFiles(fixture);
      const closingDownload = closingPage.waitForEvent('download');
      await closingPage.locator('#submit').click();
      const handedOff = await closingDownload;
      await closingPage.close();
      await handedOff.saveAs('/tmp/image-download-feasibility/chrome-after-close.png');
      check(await handedOff.failure() === null, 'handed-off download completes after actual page closure');
    } finally {
      if (!closingPage.isClosed()) await closingPage.close();
    }
    return { results, downloads: downloads.length };
  } finally {
    page.off('download', onDownload);
  }
}
