wrk.method = "POST"
wrk.headers["Content-Type"] = "application/json"

counter = 0

function request()
    counter = counter + 1
    wrk.body = '{"url": "https://example.com/page/' .. counter .. '"}'
    return wrk.format(nil, "/shorten")
end
