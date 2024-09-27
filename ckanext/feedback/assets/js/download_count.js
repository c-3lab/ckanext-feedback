async function downloadCountUp(resourceId) {
  await fetch(`${resourceId}/${'download-countup'}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify({
      resourceId: resourceId
    }),
  });
}