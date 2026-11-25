Design Music Search, Playlists, and Playback

Design an in-memory music application that searches catalog entities, manages ordered playlists, and controls one listener's playback session.

Problem statement
For this exercise, assume one signed-in listener uses an in-memory music application. A nonempty query can search songs, artists, and albums; matching and ranking are supplied by a catalog-search dependency. The listener can create owned playlists and add, remove, or reorder song entries.

A playlist is ordered, and repeated songs are allowed as distinct entry identities. The listener has one playback session with idle, playing, and paused states. Playing a different song starts it at position zero; playing the same paused song resumes it. Pause preserves the current position.

Reset keeps the song loaded, sets its position to zero, and leaves it paused. Invalid catalog identifiers and audio-engine failures return explicit errors without partially changing playlist or playback state.

Authentication, persistence, networking, audio streaming implementation, sharing, recommendations, downloads, and a multi-song playback queue are out of scope. Design the objects, responsibilities, public interfaces, state transitions, and one complete interaction flow; no implementation code is required.