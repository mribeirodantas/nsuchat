# Not So Unsafe Chat (NSUChat)

Not So Unsafe Chat (NSUChat) is a chat application developed as a final
project of a Computer Networks class at University. The goal was to
have a chat application with its own application protocol and a secret
symmetric key that all users would share in order to talk with secrecy,
in relation to people outside the chat.

Since the chat would be open to anyone with a client to connect, this
secrecy was rather limited. Apart from that, what was the purpose of
having private messages if they could be broken if all users shared
the same symmetric key?

Based on that, I developed a chat application where each user would have
its own personal symmetric key and the server would be in charge of
handling encryption/decryption for the transmission of such messages.

Assymmetric criptography was theoretically used in order to pass the
symmetric key to the server, but hasn't been implemented yet. Data
integrity through SHA-1 was partially developed, but the part of
checking wasn't done. Since I had a short deadline to develop such
software, I didn't manage to finish the aspects that were beyound
what was asked by my professor. Every once in a while, I may come here
and commit something but it will depend on my spare time from now on :-)
