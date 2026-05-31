const blockedFiles = new Set([
  ['coco', 'dot', 'to', 'dot', 'pack'].join('-') + '.pdf',
  ['coco', 'dot', 'to', 'dot', 'preview'].join('-') + '.gif',
]);

export async function onRequest(context) {
  const pathname = new URL(context.request.url).pathname;
  const filename = decodeURIComponent(pathname.split('/').pop() || '');

  if (blockedFiles.has(filename)) {
    return new Response('Not found', {
      status: 404,
      headers: {
        'Cache-Control': 'no-store',
      },
    });
  }

  return context.next();
}
