<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta
      name="viewport"
      content="width=device-width,initial-scale=1,shrink-to-fit=no,user-scalable=no"
    />
    <meta name="theme-color" content="#FFFFFF" />

    <!-- Favicons / PWA -->
    <link
      id="favicon"
      rel="icon"
      type="image/svg+xml"
      href="https://orcamentos-clinicas-ibne2gwveka9epyelt87lq.streamlit.app/-/build/favicon.svg"
    />
    <link
      id="alternate-favicon"
      rel="alternate icon"
      type="image/x-icon"
      href="https://orcamentos-clinicas-ibne2gwveka9epyelt87lq.streamlit.app/-/build/favicon.ico"
    />
    <link
      rel="mask-icon"
      href="https://orcamentos-clinicas-ibne2gwveka9epyelt87lq.streamlit.app/favicon_safari_mask.png"
      color="#FF2B2B"
    />
    <link
      rel="apple-touch-icon"
      sizes="256x256"
      href="https://orcamentos-clinicas-ibne2gwveka9epyelt87lq.streamlit.app/-/build/favicon_256.png"
    />
    <link
      rel="manifest"
      href="https://orcamentos-clinicas-ibne2gwveka9epyelt87lq.streamlit.app/-/build/manifest.json"
    />

    <!-- Google Tag Manager -->
    <script>
      ;(function (w, d, s, l, i) {
        w[l] = w[l] || []
        w[l].push({ 'gtm.start': new Date().getTime(), event: 'gtm.js' })
        var f = d.getElementsByTagName(s)[0],
          j = d.createElement(s),
          dl = l != 'dataLayer' ? '&l=' + l : ''
        j.async = true
        j.src = 'https://www.googletagmanager.com/gtm.js?id=' + i + dl
        f.parentNode.insertBefore(j, f)
      })(window, document, 'script', 'dataLayer', 'GTM-52GRQSL')
    </script>
    <!-- End Google Tag Manager -->

    <!-- Segment -->
    <script>
      !(function () {
        var analytics = (window.analytics = window.analytics || [])
        if (!analytics.initialize)
          if (analytics.invoked)
            window.console &&
              console.error &&
              console.error('Segment snippet included twice.')
          else {
            analytics.invoked = !0
            analytics.methods = [
              'trackSubmit',
              'trackClick',
              'trackLink',
              'trackForm',
              'pageview',
              'identify',
              'reset',
              'group',
              'track',
              'ready',
              'alias',
              'debug',
              'page',
              'once',
              'off',
              'on',
              'addSourceMiddleware',
              'addIntegrationMiddleware',
              'setAnonymousId',
              'addDestinationMiddleware',
            ]
            analytics.factory = function (e) {
              return function () {
                var t = Array.prototype.slice.call(arguments)
                t.unshift(e)
                analytics.push(t)
                return analytics
              }
            }
            for (var e = 0; e < analytics.methods.length; e++) {
              var key = analytics.methods[e]
              analytics[key] = analytics.factory(key)
            }
            analytics.load = function (key, e) {
              var t = document.createElement('script')
              t.type = 'text/javascript'
              t.async = !0
              t.src =
                'https://cdn.segment.com/analytics.js/v1/' +
                key +
                '/analytics.min.js'
              var n = document.getElementsByTagName('script')[0]
              n.parentNode.insertBefore(t, n)
              analytics._loadOptions = e
            }
            analytics.SNIPPET_VERSION = '4.13.1'
            analytics.load('GI7vYWHNmWwHbyFjBrvL0jOBA1TpZOXC')
            // analytics.page()
          }
      })()
    </script>
    <!-- End Segment -->

    <!-- App bundle -->
    <script
      type="module"
      crossorigin
      src="https://orcamentos-clinicas-ibne2gwveka9epyelt87lq.streamlit.app/-/build/assets/index-B59N3yFD.js"
    ></script>
    <link
      rel="stylesheet"
      crossorigin
      href="https://orcamentos-clinicas-ibne2gwveka9epyelt87lq.streamlit.app/-/build/assets/index-CJlxgJwY.css"
    />
  </head>

  <body>
    <!-- Google Tag Manager (noscript) -->
    <noscript>
      <iframe
        src="https://www.googletagmanager.com/ns.html?id=GTM-52GRQSL"
        height="0"
        width="0"
        style="display: none; visibility: hidden"
      ></iframe>
    </noscript>
    <!-- End Google Tag Manager (noscript) -->

    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>

    <!-- Status page embed -->
    <script src="https://www.streamlitstatus.com/embed/script.js"></script>
  </body>
</html>
