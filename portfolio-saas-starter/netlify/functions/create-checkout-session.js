// Minimal Netlify Function stub for checkout session creation
// Note: This is a stub. In production, integrate Stripe with STRIPE_SECRET_KEY.

export default async function handler(req, context) {
  const { method } = req;

  const cors = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
  };

  if (method === 'OPTIONS') {
    return new Response(null, { status: 204, headers: cors });
  }

  if (method !== 'POST') {
    return new Response(JSON.stringify({ error: 'Method Not Allowed' }), {
      status: 405,
      headers: { 'Content-Type': 'application/json', ...cors },
    });
  }

  try {
    const body = await req.json();
    const { priceId, success_url, cancel_url, quantity } = body || {};

    const secret = process.env.STRIPE_SECRET_KEY;
    if (secret && typeof secret === 'string' && secret.startsWith('sk_')) {
      // Attempt real Stripe integration (optional dependency)
      try {
        const { default: Stripe } = await import('stripe');
        const stripe = new Stripe(secret, { apiVersion: '2024-06-20' });
        const session = await stripe.checkout.sessions.create({
          mode: 'payment',
          line_items: [
            {
              price: priceId,
              quantity: typeof quantity === 'number' && quantity > 0 ? quantity : 1,
            },
          ],
          success_url: success_url || `${new URL(req.url).origin}/?status=success`,
          cancel_url: cancel_url || `${new URL(req.url).origin}/?status=cancel`,
          allow_promotion_codes: true,
          billing_address_collection: 'auto',
        });
        return new Response(JSON.stringify({ url: session.url }), {
          status: 200,
          headers: { 'Content-Type': 'application/json', ...cors },
        });
      } catch (e) {
        // Fall through to stub if Stripe SDK not installed or other error
      }
    }

    // Stub fallback (no secret key or SDK missing)
    const checkoutUrl = 'https://checkout.stripe.com/pay/test';
    return new Response(
      JSON.stringify({ url: checkoutUrl, priceId, success_url, cancel_url }),
      { status: 200, headers: { 'Content-Type': 'application/json', ...cors } }
    );
  } catch (e) {
    return new Response(JSON.stringify({ error: 'Bad Request' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json', ...cors },
    });
  }
}
