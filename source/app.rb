# frozen_string_literal: true

require 'json'

# Rack application for the kosli-demo base service. Serves the two health probes
# (/alive, /ready) and the two datetime.txt-backed endpoints (/repo-name,
# /timestamp) that the rest of the demo reads. Every response is JSON. This is
# the Ruby reimplementation of the former static C server; the routes and their
# response bodies are unchanged.
class App
  DATETIME_FILE = File.join(__dir__, 'datetime.txt')

  # Rack entry point. Only GET is served; each known path maps to a handler and
  # anything else is a 404. Returns the [status, headers, body] triple Rack
  # expects.
  def call(env)
    return not_found unless env['REQUEST_METHOD'] == 'GET'

    case env['PATH_INFO']
    when '/alive'     then json(200, { alive: true })
    when '/ready'     then ready
    when '/repo-name' then datetime_response('repo-name', :name)
    when '/timestamp' then datetime_response('timestamp', :timestamp)
    else not_found
    end
  end

  private

  # Readiness probe: 200 when datetime.txt is present and well-formed, 503 with
  # a reason otherwise. Fails toward not-ready so the container is never falsely
  # reported ready.
  def ready
    read_datetime
    json(200, { ready: true })
  rescue StandardError => e
    json(503, { ready: false, reason: e.message })
  end

  # Serves one field of datetime.txt under the given JSON key, or 503 when the
  # file cannot be read.
  def datetime_response(key, field)
    json(200, { key => read_datetime.fetch(field) })
  rescue StandardError
    json(503, { detail: 'cannot read datetime.txt' })
  end

  # Reads datetime.txt and returns its two whitespace-separated words as
  # { name:, timestamp: }. Raises when the file is missing or has fewer than two
  # words.
  def read_datetime
    words = File.read(DATETIME_FILE).split
    raise 'datetime.txt must contain two words' if words.size < 2

    { name: words[0], timestamp: words[1] }
  end

  # Builds the Rack response triple for a JSON body.
  def json(status, hash)
    [status, { 'content-type' => 'application/json' }, [JSON.generate(hash)]]
  end

  # 404 JSON response for unknown paths and non-GET methods.
  def not_found
    json(404, { detail: 'Not Found' })
  end
end
