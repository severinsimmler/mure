/* @name create_table */
CREATE TABLE IF NOT EXISTS response (
    key TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    headers TEXT NOT NULL,
    status INTEGER NOT NULL,
    ok BOOLEAN NOT NULL,
    reason TEXT,
    content BLOB NOT NULL,
    encoding TEXT
);


/* @name save_response */
INSERT INTO
    response (
        key,
        url,
        headers,
        status,
        ok,
        reason,
        content,
        encoding
    )
VALUES
    (
        :key,
        :url,
        :headers,
        :status,
        :ok,
        :reason,
        :content,
        :encoding
    ) ON CONFLICT(key) DO
UPDATE
SET
    url = :url,
    headers = :headers,
    status = :status,
    ok = :ok,
    reason = :reason,
    content = :content,
    encoding = :encoding;


/* @name get_response */
SELECT
    url,
    headers,
    status,
    ok,
    reason,
    content,
    encoding
FROM
    response
WHERE
    key = :key;
