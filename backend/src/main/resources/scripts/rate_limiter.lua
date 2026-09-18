-- Distributed Token Bucket Rate Limiter in Redis Lua
-- Keys:
--   KEYS[1]: Rate limit key (e.g., rl:upload:<tenant_id>:<user_id>)
-- Arguments:
--   ARGV[1]: Bucket capacity (max tokens)
--   ARGV[2]: Refill rate in tokens per second (float or integer)
--   ARGV[3]: Current timestamp in seconds (float or integer)
--   ARGV[4]: Requested tokens (usually 1)
--   ARGV[5]: Redis key TTL / expiration in seconds

local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])
local ttl = tonumber(ARGV[5])

local data = redis.call("HMGET", key, "tokens", "last_updated")
local tokens = tonumber(data[1])
local last_updated = tonumber(data[2])

if tokens == nil then
    tokens = capacity
    last_updated = now
else
    local elapsed = math.max(0, now - last_updated)
    tokens = math.min(capacity, tokens + (elapsed * refill_rate))
    last_updated = now
end

if tokens >= requested then
    tokens = tokens - requested
    redis.call("HMSET", key, "tokens", tokens, "last_updated", last_updated)
    redis.call("EXPIRE", key, ttl)
    return {1, math.floor(tokens), 0} -- [allowed: 1, remaining: tokens, retry_after: 0]
else
    local missing = requested - tokens
    local retry_after = math.ceil(missing / refill_rate)
    return {0, math.floor(tokens), retry_after} -- [allowed: 0, remaining: tokens, retry_after: seconds]
end
